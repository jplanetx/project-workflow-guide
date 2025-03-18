#!/usr/bin/env python
import sys
import os
import json
import time
import asyncio
import httpx
from datetime import datetime
from configparser import ConfigParser
from dotenv import load_dotenv

# Import our custom logger and AI-related modules
from task_logger import setup_logger
from token_tracker import TokenTracker
import ai_agents

# Set up logger
logger = setup_logger('start_task')

# Initialize token tracker
token_tracker = TokenTracker()

async def load_config():
    """Load GitHub configuration asynchronously"""
    # Load environment variables from .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    
    # Get GitHub token from environment variable
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token or github_token == 'your_github_token_here':
        logger.error("GitHub token not found in .env file")
        logger.info(f"Please update your token in {env_path}")
        return None
    
    # Load other configuration from config.ini
    config = ConfigParser()
    config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    if not os.path.exists(config_file):
        # Create default config file
        config['github'] = {
            'owner': 'YOUR_GITHUB_USERNAME',
            'repo': 'YOUR_REPO_NAME'
        }
        with open(config_file, 'w') as f:
            config.write(f)
        logger.error(f"Please update GitHub repository details in {config_file}")
        return None
    
    config.read(config_file)
    
    # Combine token from .env with other settings from config.ini
    github_config = {
        'token': github_token,
        'owner': config['github']['owner'],
        'repo': config['github']['repo']
    }
    
    return github_config

async def check_duplicate_issues(title, config):
    """Check if an issue with the same title already exists using async HTTP."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    search_url = f"https://api.github.com/search/issues?q=repo:{config['owner']}/{config['repo']}+is:issue+\"{title}\""
    
    async with httpx.AsyncClient() as client:
        for attempt in range(3):  # Max 3 retries
            try:
                logger.debug(f"Checking for duplicate issues with title: {title}")
                response = await client.get(search_url, headers=headers)
                response.raise_for_status()
                search_results = response.json()
                
                for item in search_results['items']:
                    if item['title'].lower() == title.lower():
                        logger.info(f"Found existing issue with the same title: #{item['number']}")
                        return item['number'], item['html_url']
                
                logger.debug("No duplicate issues found")
                return None, None
                
            except httpx.HTTPStatusError as e:
                logger.warning(f"Attempt {attempt + 1}/3 failed when checking for duplicates: {e}")
                if attempt < 2:  # Only retry if we haven't done 3 attempts yet
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to check for duplicate issues after 3 attempts")
                    return None, None

async def create_github_issue(title, config, related_issues=None):
    """Create a GitHub issue using the API with async HTTP."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Base issue template
    issue_template = f"""## Task Description
[Add detailed description here]

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

"""

    # Add related issues section if available
    if related_issues and len(related_issues) > 0:
        issue_template += "## Related Issues\n"
        for issue in related_issues[:5]:  # Limit to top 5 most relevant issues
            status_icon = "🟢" if issue['state'] == 'open' else "🔴"
            issue_template += f"- {status_icon} #{issue['number']} [{issue['title']}]({issue['url']}) (Relevance: {issue['relevance']})\n"
        issue_template += "\n"
    
    # Add standard footer
    issue_template += f"""## Additional Notes
- Created via task automation script
- Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- AI context priming available in docs/context_priming.md
- AI-generated code snippets available in docs/ai_output/
"""
    
    data = {
        'title': title,
        'body': issue_template,
        'labels': ['Task']
    }
    
    url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues"
    
    async with httpx.AsyncClient() as client:
        for attempt in range(3):  # Max 3 retries
            try:
                logger.debug(f"Attempting to create GitHub issue: {title}")
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                issue = response.json()
                logger.info(f"Successfully created GitHub issue #{issue['number']}")
                return issue['number'], issue['html_url']
            except httpx.HTTPStatusError as e:
                logger.warning(f"Attempt {attempt + 1}/3 failed: {e}")
                if attempt < 2:  # Only retry if we haven't done 3 attempts yet
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to create GitHub issue after 3 attempts")
                    return None, None

async def find_related_issues(task_title, config):
    """Find issues related to a given task title."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Extract keywords from the task title
    keywords = [word.lower() for word in task_title.split() if len(word) > 3]
    if not keywords:
        keywords = [task_title.lower()]
    
    # Create a search query with keywords
    keywords_query = ' OR '.join(keywords)
    search_url = f"https://api.github.com/search/issues?q=repo:{config['owner']}/{config['repo']}+is:issue+{keywords_query}"
    
    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Searching for issues related to: {task_title}")
            response = await client.get(search_url, headers=headers)
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
                
                # Simple relevance calculation
                title_words = set(item['title'].lower().split())
                keywords_set = set(keywords)
                
                # Calculate overlap between title words and keywords
                common_words = title_words.intersection(keywords_set)
                if len(common_words) > 0:
                    relevance = len(common_words) / max(len(keywords_set), len(title_words))
                    
                    # Only include issues with relevance above threshold
                    if relevance >= 0.3:  # Lower threshold to find more related issues
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
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error searching for related issues: {e}")
            return []

async def collect_project_data(task_title):
    """Collect project data for AI context using the CollectorAgent."""
    logger.info(f"Collecting project data for task: {task_title}")
    
    try:
        # Use the collector agent to gather all project data in parallel
        context_file = os.path.join("docs", "context_priming.md")
        results = await ai_agents.run_collector_agent(
            task_id="context_priming",
            task_title=task_title,
            output_file=context_file
        )
        
        if "error" in results:
            logger.error(f"Error during context collection: {results['error']}")
            return None, None
        
        logger.info(f"AI context primer generated: {context_file}")
        return context_file, results
    
    except Exception as e:
        logger.error(f"Error collecting project data: {e}")
        return None, None

async def generate_code_stubs(task_id, task_title, context_data):
    """Generate code stubs using the ExecutorAgent."""
    logger.info(f"Generating code stubs for task: {task_title}")
    
    try:
        # Use the executor agent to generate code stubs
        output_dir = os.path.join("docs", "ai_output")
        results = await ai_agents.run_executor_agent(
            task_type="code_generation",
            task_id=task_id,
            task_title=task_title,
            context=context_data,
            output_dir=output_dir
        )
        
        if "error" in results:
            logger.error(f"Error generating code stubs: {results['error']}")
            return None
        
        logger.info(f"Generated code stubs saved to {output_dir}")
        return results.get("saved_files", [])
    
    except Exception as e:
        logger.error(f"Error generating code stubs: {e}")
        return None

async def main():
    if len(sys.argv) < 2:
        logger.error("Missing required argument: task title")
        print("Usage: start_task.py 'Task Title'")
        sys.exit(1)

    task_title = sys.argv[1]
    logger.info(f"Starting task: {task_title}")
    
    # Load GitHub configuration
    config = await load_config()
    if not config:
        logger.error("Failed to load configuration")
        sys.exit(1)
    
    logger.debug("Configuration loaded successfully")
    
    # Check for duplicate issues first
    duplicate_number, duplicate_url = await check_duplicate_issues(task_title, config)
    if duplicate_number:
        logger.warning(f"An issue with this title already exists: #{duplicate_number}")
        print(f"Issue already exists with the same title: #{duplicate_number}")
        print(f"URL: {duplicate_url}")
        use_existing = input("Would you like to use this existing issue? (y/n): ").lower()
        
        if use_existing == 'y':
            issue_number = duplicate_number
            issue_url = duplicate_url
        else:
            print("Exiting without creating a new issue.")
            sys.exit(0)
    else:
        # Run context collection and issue search in parallel
        logger.info(f"Generating AI context and searching for related issues in parallel")
        print("Generating AI context and searching for related issues in parallel...")
        
        # Gather all tasks simultaneously
        context_task = collect_project_data(task_title)
        related_issues_task = find_related_issues(task_title, config)
        
        # Wait for both to complete
        context_file, context_data = await context_task
        related_issues = await related_issues_task
        
        if context_file:
            print(f"AI context primer generated: {context_file}")
        else:
            print("Warning: Failed to generate AI context primer")
        
        if related_issues:
            print(f"Found {len(related_issues)} related issues")
        else:
            print("No related issues found")
        
        # Create GitHub issue with related issues included
        issue_number, issue_url = await create_github_issue(task_title, config, related_issues)
        
        if not issue_number:
            logger.error("Failed to create GitHub issue")
            print("Failed to create GitHub issue. Please check the logs for details.")
            sys.exit(1)
        
        # Generate code stubs in parallel
        print("Generating AI code stubs and test templates...")
        code_files = await generate_code_stubs(str(issue_number), task_title, context_data)
        
        if code_files:
            print(f"Generated {len(code_files)} code files for the task")
        else:
            print("Note: No code files were generated")
    
    if issue_number:
        # Create local task file
        task_filename = os.path.join("docs", "tasks", f"TASK-{issue_number}.md")
        
        # Get path to context primer file
        context_primer_path = os.path.join("docs", "context_priming.md")
        context_primer_rel_path = os.path.relpath(context_primer_path, os.path.dirname(task_filename))
        
        # Get path to AI output directory
        ai_output_dir = os.path.join("docs", "ai_output")
        ai_output_rel_path = os.path.relpath(ai_output_dir, os.path.dirname(task_filename))
        
        task_template = f"""# {task_title}

## Task Details
- **Issue:** #{issue_number}
- **URL:** {issue_url}
- **Created:** {datetime.now().strftime('%Y-%m-%d')}
- **AI Context Primer:** [{os.path.basename(context_primer_path)}]({context_primer_rel_path})
- **AI Generated Code:** [{os.path.basename(ai_output_dir)}]({ai_output_rel_path})

## Implementation Notes
- Describe your planned approach, key decisions, and any challenges you anticipate.
- Reference AI-generated code stubs if helpful.

## Testing Steps
- Outline the steps required to test the implementation.
- Consider using AI-generated test templates as a starting point.

## Verification Results
- Record the outcomes of your testing and verification checks.

## Token Usage
- Token usage is being tracked in logs/token_usage/
- Run `python scripts/token_tracker.py report task {issue_number}` to view usage stats
"""
        try:
            os.makedirs(os.path.dirname(task_filename), exist_ok=True)
            with open(task_filename, "w") as f:
                f.write(task_template)
            logger.info(f"Task file {task_filename} created successfully")
            print(f"Task file {task_filename} created successfully.")
        except Exception as e:
            logger.error(f"Failed to create task file: {e}")
            print(f"Error creating task file: {e}")
    else:
        logger.error("Failed to create or find GitHub issue")
        print("Failed to create GitHub issue. Please check the logs for details.")

if __name__ == "__main__":
    asyncio.run(main())