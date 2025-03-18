#!/usr/bin/env python
import sys
import os
import json
import time
import asyncio
import httpx
import re
from datetime import datetime
from configparser import ConfigParser
from dotenv import load_dotenv
from difflib import SequenceMatcher

# Import our custom logger and AI-related modules
from scripts.task_logger import setup_logger
from scripts.token_tracker import TokenTracker
from scripts import ai_agents

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

def calculate_similarity(text1, text2):
    """Calculate text similarity using SequenceMatcher."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def tokenize_text(text):
    """Tokenize text by removing common stop words and keeping meaningful words."""
    # Simple list of stop words to exclude
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'in', 'to', 'for', 'with', 'on', 'at'}
    
    # Clean text - remove punctuation and split into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Remove stop words and words less than 3 chars
    tokens = [word for word in words if word not in stop_words and len(word) >= 3]
    
    return tokens

def calculate_token_similarity(tokens1, tokens2):
    """Calculate the similarity based on shared tokens."""
    if not tokens1 or not tokens2:
        return 0.0
    
    set1 = set(tokens1)
    set2 = set(tokens2)
    
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    # Token overlap ratio
    jaccard_index = len(intersection) / len(union) if union else 0
    
    # Weighted by number of common tokens
    return jaccard_index * (1 + 0.1 * len(intersection))

async def find_similar_issues(title, config, similarity_threshold=0.7):
    """Find issues with similar titles using fuzzy matching."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Extract tokens from the query title
    query_tokens = tokenize_text(title)
    
    # Get all open issues from the repository
    issues_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues?state=all&per_page=100"
    
    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Searching for issues similar to: {title}")
            response = await client.get(issues_url, headers=headers)
            response.raise_for_status()
            all_issues = response.json()
            
            # Filter out pull requests
            issues = [issue for issue in all_issues if 'pull_request' not in issue]
            
            if not issues:
                logger.info("No issues found in the repository")
                return None, None, []
            
            # Calculate similarity for each issue
            similar_issues = []
            exact_match = None
            exact_match_url = None
            highest_similarity = 0
            highest_sim_issue = None
            
            for issue in issues:
                issue_title = issue['title']
                
                # Check for exact match first (case insensitive)
                if issue_title.lower() == title.lower():
                    exact_match = issue['number']
                    exact_match_url = issue['html_url']
                    logger.info(f"Found exact match: #{issue['number']} - {issue_title}")
                
                # Calculate similarity scores
                string_similarity = calculate_similarity(title, issue_title)
                
                # Token-based similarity
                issue_tokens = tokenize_text(issue_title)
                token_similarity = calculate_token_similarity(query_tokens, issue_tokens)
                
                # Combined similarity score (weighted)
                combined_similarity = 0.4 * string_similarity + 0.6 * token_similarity
                
                # Track highest similarity issue
                if combined_similarity > highest_similarity:
                    highest_similarity = combined_similarity
                    highest_sim_issue = issue
                
                # Add to similar issues if above threshold
                if combined_similarity >= similarity_threshold:
                    similar_issues.append({
                        'number': issue['number'],
                        'title': issue_title,
                        'state': issue['state'],
                        'created_at': issue['created_at'],
                        'url': issue['html_url'],
                        'similarity': round(combined_similarity, 2)
                    })
            
            # Sort similar issues by similarity score
            similar_issues.sort(key=lambda x: x['similarity'], reverse=True)
            
            # If no exact match but we have a very similar issue (>0.85 similarity)
            if not exact_match and highest_similarity > 0.85 and highest_sim_issue:
                logger.info(f"Found highly similar issue: #{highest_sim_issue['number']} - {highest_sim_issue['title']} (similarity: {highest_similarity:.2f})")
                return highest_sim_issue['number'], highest_sim_issue['html_url'], similar_issues
            
            return exact_match, exact_match_url, similar_issues
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error searching for similar issues: {e}")
            return None, None, []

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
            similarity_pct = f"{issue['similarity'] * 100:.0f}%" if 'similarity' in issue else f"{issue.get('relevance', 0) * 100:.0f}%"
            issue_template += f"- {status_icon} #{issue['number']} [{issue['title']}]({issue['url']}) (Similarity: {similarity_pct})\n"
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
    """Find issues related to a given task title but not necessarily similar."""
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
                    if relevance >= 0.2:  # Lower threshold to find more related issues
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
    
    # Check for similar issues first using fuzzy matching
    exact_match, exact_url, similar_issues = await find_similar_issues(task_title, config)
    
    issue_number = None
    issue_url = None
    
    if exact_match:
        logger.warning(f"An issue with this title already exists: #{exact_match}")
        print(f"Issue already exists with the same title: #{exact_match}")
        print(f"URL: {exact_url}")
        use_existing = input("Would you like to use this existing issue? (y/n): ").lower()
        
        if use_existing == 'y':
            issue_number = exact_match
            issue_url = exact_url
        else:
            print("Exiting without creating a new issue.")
            sys.exit(0)
    elif similar_issues:
        # Display similar issues
        print("\nSimilar issues found:")
        for i, issue in enumerate(similar_issues[:5], 1):  # Show top 5
            status = "OPEN" if issue['state'] == 'open' else "CLOSED"
            similarity_pct = f"{issue['similarity'] * 100:.0f}%"
            print(f"{i}. #{issue['number']} [{status}] {issue['title']} (Similarity: {similarity_pct})")
        
        print("\nOptions:")
        print("0. Create a new issue")
        for i in range(1, min(len(similar_issues[:5]) + 1, 6)):
            print(f"{i}. Link to issue #{similar_issues[i-1]['number']}")
        
        choice = input("\nChoose an option (0-5): ")
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(similar_issues[:5]):
                # User chose to link to an existing issue
                selected_issue = similar_issues[choice_num - 1]
                issue_number = selected_issue['number']
                issue_url = selected_issue['url']
                print(f"Using existing issue #{issue_number}")
            else:
                # User chose to create a new issue
                print("Creating a new issue...")
                # Continue to issue creation below
        except ValueError:
            # Default to creating a new issue if input is invalid
            print("Invalid choice. Creating a new issue...")
    
    if not issue_number:
        # Run context collection and issue search in parallel
        logger.info(f"Generating AI context and searching for related issues in parallel")
        print("Generating AI context and searching for related issues in parallel...")
        
        # Gather all tasks simultaneously
        context_task = collect_project_data(task_title)
        related_issues_task = find_related_issues(task_title, config)
        
        # Wait for both to complete
        context_file, context_data = await context_task
        related_issues = await related_issues_task
        
        # Combine similar and related issues, prioritizing similar ones
        all_issues = similar_issues.copy() if similar_issues else []
        
        # Add related issues that aren't already in similar issues
        if related_issues:
            similar_numbers = {issue['number'] for issue in all_issues}
            for issue in related_issues:
                if issue['number'] not in similar_numbers:
                    all_issues.append(issue)
        
        # Sort all issues by similarity/relevance (highest first)
        all_issues.sort(key=lambda x: x.get('similarity', x.get('relevance', 0)), reverse=True)
        
        if context_file:
            print(f"AI context primer generated: {context_file}")
        else:
            print("Warning: Failed to generate AI context primer")
        
        if all_issues:
            print(f"Found {len(all_issues)} similar or related issues")
        else:
            print("No similar or related issues found")
        
        # Create GitHub issue with related issues included
        issue_number, issue_url = await create_github_issue(task_title, config, all_issues)
        
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