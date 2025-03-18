#!/usr/bin/env python
import os
import sys
import json
import requests
import time
from datetime import datetime
from configparser import ConfigParser
from dotenv import load_dotenv

# Import our custom logger
from task_logger import setup_logger

# Set up logger
logger = setup_logger('context_priming')

def load_config():
    # Load environment variables from .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    
    # Get GitHub token from environment variable
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token or github_token == 'your_github_token_here':
        logger.error("GitHub token not found in .env file")
        logger.info(f"Please update your token in {env_path}")
        sys.exit(1)
    
    # Load other configuration from config.ini
    config = ConfigParser()
    config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    if not os.path.exists(config_file):
        logger.error(f"Config file {config_file} does not exist")
        print(f"Config file {config_file} does not exist. Please create it first.")
        sys.exit(1)
    
    config.read(config_file)
    
    # Combine token from .env with other settings from config.ini
    github_config = {
        'token': github_token,
        'owner': config['github']['owner'],
        'repo': config['github']['repo']
    }
    
    return github_config

def get_repo_readme(config, max_retries=3):
    """Fetch the repository README.md content from GitHub."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    readme_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/readme"
    
    for attempt in range(max_retries):
        try:
            logger.debug("Fetching repository README")
            response = requests.get(readme_url, headers=headers)
            response.raise_for_status()
            readme_data = response.json()
            
            # GitHub returns README content as base64 encoded
            import base64
            readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
            logger.info("Successfully fetched README.md")
            return readme_content
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed when fetching README: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch README after {max_retries} attempts")
                return "Unable to fetch README content"

def get_recent_commits(config, limit=10, max_retries=3):
    """Fetch recent commits from the repository."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    commits_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/commits?per_page={limit}"
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Fetching recent {limit} commits")
            response = requests.get(commits_url, headers=headers)
            response.raise_for_status()
            commits = response.json()
            
            # Extract relevant info from each commit
            commit_summaries = []
            for commit in commits:
                commit_summaries.append({
                    'sha': commit['sha'][:7],
                    'message': commit['commit']['message'].split('\n')[0],  # First line of commit message
                    'author': commit['commit']['author']['name'],
                    'date': commit['commit']['author']['date'],
                    'url': commit['html_url']
                })
            
            logger.info(f"Successfully fetched {len(commit_summaries)} commits")
            return commit_summaries
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed when fetching commits: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch commits after {max_retries} attempts")
                return []

def get_recent_issues(config, state="all", limit=10, max_retries=3):
    """Fetch recent issues from the repository."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    issues_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues?state={state}&per_page={limit}"
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Fetching recent {limit} {state} issues")
            response = requests.get(issues_url, headers=headers)
            response.raise_for_status()
            issues = response.json()
            
            # Extract relevant info from each issue
            issue_summaries = []
            for issue in issues:
                # Skip pull requests
                if 'pull_request' in issue:
                    continue
                    
                issue_summaries.append({
                    'number': issue['number'],
                    'title': issue['title'],
                    'state': issue['state'],
                    'created_at': issue['created_at'],
                    'updated_at': issue['updated_at'],
                    'url': issue['html_url'],
                    'labels': [label['name'] for label in issue['labels']]
                })
            
            logger.info(f"Successfully fetched {len(issue_summaries)} issues")
            return issue_summaries
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed when fetching issues: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch issues after {max_retries} attempts")
                return []

def get_task_related_issues(task_title, config, max_retries=3, similarity_threshold=0.5):
    """Find issues related to a given task title."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Extract keywords from the task title (simple implementation)
    keywords = [word.lower() for word in task_title.split() if len(word) > 3]
    if not keywords:
        keywords = [task_title.lower()]
    
    # Create a search query with keywords
    keywords_query = ' OR '.join(keywords)
    search_url = f"https://api.github.com/search/issues?q=repo:{config['owner']}/{config['repo']}+is:issue+{keywords_query}"
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Searching for issues related to: {task_title}")
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            search_results = response.json()
            
            if search_results['total_count'] == 0:
                logger.info(f"No issues found related to '{task_title}'")
                return []
                
            related_issues = []
            for item in search_results['items']:
                # Skip pull requests
                if 'pull_request' in item:
                    continue
                
                # Simple relevance calculation (can be enhanced with NLP in production)
                title_words = set(item['title'].lower().split())
                keywords_set = set(keywords)
                
                # Calculate overlap between title words and keywords
                common_words = title_words.intersection(keywords_set)
                if len(common_words) > 0:
                    relevance = len(common_words) / max(len(keywords_set), len(title_words))
                    
                    # Only include issues with relevance above threshold
                    if relevance >= similarity_threshold:
                        related_issues.append({
                            'number': item['number'],
                            'title': item['title'],
                            'state': item['state'],
                            'created_at': item['created_at'],
                            'url': item['html_url'],
                            'relevance': round(relevance, 2)
                        })
            
            if related_issues:
                logger.info(f"Found {len(related_issues)} related issues")
                # Sort by relevance (highest first)
                related_issues.sort(key=lambda x: x['relevance'], reverse=True)
            else:
                logger.info(f"No related issues found with sufficient relevance")
                
            return related_issues
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed when searching for related issues: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to search for related issues after {max_retries} attempts")
                return []

def get_project_directory_structure(max_depth=3):
    """Get the directory structure of the project."""
    root_dir = os.path.join(os.path.dirname(__file__), '..')
    root_dir = os.path.abspath(root_dir)
    
    def generate_structure(directory, depth=0):
        if depth > max_depth:
            return "..."
        
        structure = []
        try:
            for item in os.listdir(directory):
                # Skip hidden files and directories
                if item.startswith('.'):
                    continue
                    
                full_path = os.path.join(directory, item)
                if os.path.isdir(full_path):
                    # For directories, recursively explore
                    sub_structure = generate_structure(full_path, depth + 1)
                    structure.append({item + '/': sub_structure})
                else:
                    # For files, just add the name
                    structure.append(item)
        except Exception as e:
            logger.error(f"Error accessing directory {directory}: {e}")
            return ["Error accessing directory"]
        
        return structure
    
    logger.debug("Generating project directory structure")
    directory_structure = generate_structure(root_dir)
    logger.info("Successfully generated directory structure")
    return directory_structure

def generate_context_primer(task_title=None):
    """Generate a context primer that combines all relevant project data."""
    logger.info("Generating context primer")
    
    try:
        config = load_config()
        logger.debug("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Collect all the data
    readme_content = get_repo_readme(config)
    recent_commits = get_recent_commits(config)
    recent_issues = get_recent_issues(config, state="all", limit=10)
    directory_structure = get_project_directory_structure()
    
    # Get task-related issues if a task title is provided
    related_issues = []
    if task_title:
        related_issues = get_task_related_issues(task_title, config)
    
    # Format the context primer
    context_primer = "# AI Context Primer\n\n"
    context_primer += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    # Add task-specific information if a title was provided
    if task_title:
        context_primer += f"## Current Task: {task_title}\n\n"
        
        if related_issues:
            context_primer += "### Related Issues\n\n"
            for issue in related_issues:
                status_icon = "🟢" if issue['state'] == 'open' else "🔴"
                context_primer += f"- {status_icon} #{issue['number']} [{issue['title']}]({issue['url']}) (Relevance: {issue['relevance']})\n"
            context_primer += "\n"
    
    # Add project overview from README
    context_primer += "## Project Overview\n\n"
    context_primer += readme_content + "\n\n"
    
    # Add recent commit history
    context_primer += "## Recent Commits\n\n"
    for commit in recent_commits:
        context_primer += f"- [{commit['sha']}] {commit['message']} - *{commit['author']}* on {commit['date'].split('T')[0]}\n"
    context_primer += "\n"
    
    # Add recent issues
    context_primer += "## Recent Issues\n\n"
    for issue in recent_issues:
        status_icon = "🟢" if issue['state'] == 'open' else "🔴"
        labels_str = ", ".join([f"`{label}`" for label in issue['labels']]) if issue['labels'] else ""
        context_primer += f"- {status_icon} #{issue['number']} [{issue['title']}]({issue['url']}) {labels_str}\n"
    context_primer += "\n"
    
    # Add directory structure
    context_primer += "## Project Structure\n\n```\n"
    context_primer += json.dumps(directory_structure, indent=2)
    context_primer += "\n```\n"
    
    # Save the context primer to a file
    context_primer_file = os.path.join(os.path.dirname(__file__), '..', 'docs', 'context_priming.md')
    try:
        os.makedirs(os.path.dirname(context_primer_file), exist_ok=True)
        with open(context_primer_file, 'w', encoding='utf-8') as f:
            f.write(context_primer)
        logger.info(f"Context primer saved to {context_primer_file}")
    except Exception as e:
        logger.error(f"Error saving context primer: {e}")
    
    return context_primer_file

def main():
    if len(sys.argv) > 1:
        task_title = sys.argv[1]
        logger.info(f"Generating context primer for task: {task_title}")
        context_file = generate_context_primer(task_title)
    else:
        logger.info("Generating general context primer")
        context_file = generate_context_primer()
    
    print(f"Context primer generated: {context_file}")

if __name__ == "__main__":
    main()