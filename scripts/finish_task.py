#!/usr/bin/env python
import sys
import os
import requests
import json
import glob
import time
from configparser import ConfigParser
from dotenv import load_dotenv

# Import our custom logger
from task_logger import setup_logger

# Set up logger
logger = setup_logger('finish_task')

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

def find_issues_by_title(title, config, max_retries=3):
    """Find GitHub issues by title with retry logic."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Search for issues with the given title
    search_url = f"https://api.github.com/search/issues?q=repo:{config['owner']}/{config['repo']}+is:issue+\"{title}\""
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Searching for issues with title: {title}")
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            search_results = response.json()
            
            if search_results['total_count'] == 0:
                logger.warning(f"No issues found with title: '{title}'")
                return []
                
            matching_issues = []
            for item in search_results['items']:
                # Filter to exact title matches
                if item['title'].lower() == title.lower():
                    matching_issues.append({
                        'number': item['number'],
                        'title': item['title'],
                        'state': item['state'],
                        'url': item['html_url']
                    })
            
            if matching_issues:
                logger.info(f"Found {len(matching_issues)} matching issues")
            else:
                logger.warning(f"No exact title matches found")
                
            return matching_issues
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed when searching for issues: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to search for GitHub issues after {max_retries} attempts")
                return []

def find_issue_from_local_files(title):
    """Find issue number from local task files matching title."""
    tasks_dir = os.path.join("docs", "tasks")
    if not os.path.exists(tasks_dir):
        logger.warning(f"Tasks directory not found: {tasks_dir}")
        return None
        
    task_files = glob.glob(os.path.join(tasks_dir, "TASK-*.md"))
    logger.debug(f"Found {len(task_files)} local task files")
    
    for task_file in task_files:
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Check if the first line contains the task title
                first_line = content.strip().split("\n")[0]
                if first_line.startswith("# ") and first_line[2:].lower() == title.lower():
                    # Extract issue number from filename (TASK-123.md -> 123)
                    issue_number = os.path.basename(task_file).replace("TASK-", "").replace(".md", "")
                    try:
                        issue_num = int(issue_number)
                        logger.info(f"Found matching local task file with issue #{issue_num}")
                        return issue_num
                    except ValueError:
                        logger.warning(f"Invalid issue number format in filename: {task_file}")
        except Exception as e:
            logger.error(f"Error reading task file {task_file}: {e}")
    
    logger.warning(f"No matching local task file found for title: {title}")
    return None

def add_comment_and_close_issue(issue_number, comment, config, max_retries=3):
    """Add a comment to an issue and close it with retry logic."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # First, check if the issue exists and is open
    issue_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues/{issue_number}"
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Checking issue #{issue_number} status")
            response = requests.get(issue_url, headers=headers)
            response.raise_for_status()
            issue_data = response.json()
            
            if issue_data['state'] == 'closed':
                logger.warning(f"Issue #{issue_number} is already closed")
                return False, "Issue is already closed"
            break
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed when checking issue status: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to check issue status after {max_retries} attempts")
                return False, f"Failed to check issue status: {e}"
    
    # Add a comment
    comment_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues/{issue_number}/comments"
    comment_data = {
        'body': comment
    }
    
    # Try to add a comment
    for attempt in range(max_retries):
        try:
            logger.debug(f"Adding comment to issue #{issue_number}")
            response = requests.post(comment_url, headers=headers, json=comment_data)
            response.raise_for_status()
            logger.info(f"Comment added to issue #{issue_number}")
            break
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed when adding comment: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to add comment after {max_retries} attempts")
                return False, f"Failed to add comment: {e}"
    
    # Close the issue
    close_data = {
        'state': 'closed'
    }
    
    # Try to close the issue
    for attempt in range(max_retries):
        try:
            logger.debug(f"Closing issue #{issue_number}")
            response = requests.patch(issue_url, headers=headers, json=close_data)
            response.raise_for_status()
            logger.info(f"Successfully closed issue #{issue_number}")
            return True, "Success"
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed when closing issue: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to close issue after {max_retries} attempts")
                return False, f"Failed to close issue: {e}"

def main():
    if len(sys.argv) < 2:
        logger.error("Missing required argument: task title")
        print("Usage: finish_task.py 'Task Title' ['Verification Results']")
        print("  - Task Title: Title of the task/issue to close")
        print("  - Verification Results: Optional results to add to the local task file")
        sys.exit(1)

    task_title = sys.argv[1]
    verification = sys.argv[2] if len(sys.argv) > 2 else "Task completed successfully."
    
    logger.info(f"Finishing task: {task_title}")
    
    # Load GitHub configuration
    try:
        config = load_config()
        logger.debug("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

    # Try to find issue number from local files first
    issue_number = find_issue_from_local_files(task_title)
    
    # If not found in local files, search GitHub by title
    if not issue_number:
        logger.info("Issue not found in local files, searching GitHub by title")
        matching_issues = find_issues_by_title(task_title, config)
        
        if not matching_issues:
            error_msg = f"Could not find any GitHub issue with title: '{task_title}'"
            logger.error(error_msg)
            print(error_msg)
            sys.exit(1)
        
        if len(matching_issues) > 1:
            logger.info(f"Found multiple issues ({len(matching_issues)}) with the same title")
            print(f"Found multiple issues with title '{task_title}':")
            for i, issue in enumerate(matching_issues):
                print(f"{i+1}. Issue #{issue['number']} - {issue['title']} ({issue['state']})")
            
            choice = input("Enter the number of the issue to close (or 'q' to quit): ")
            if choice.lower() == 'q':
                logger.info("User chose to quit")
                sys.exit(0)
                
            try:
                selected = int(choice) - 1
                if 0 <= selected < len(matching_issues):
                    issue_number = matching_issues[selected]['number']
                    logger.info(f"User selected issue #{issue_number}")
                else:
                    logger.error("Invalid selection")
                    print("Invalid selection.")
                    sys.exit(1)
            except ValueError:
                logger.error("Invalid input")
                print("Invalid input.")
                sys.exit(1)
        else:
            issue_number = matching_issues[0]['number']
            
            # Check if the issue is already closed
            if matching_issues[0]['state'] == 'closed':
                logger.warning(f"Issue #{issue_number} is already closed")
                print(f"Issue #{issue_number} is already closed.")
                update_local = input("Would you like to update the local task file anyway? (y/n): ")
                if update_local.lower() != 'y':
                    logger.info("User chose not to update local file")
                    sys.exit(0)
    
    # Find the local task file
    task_filename = os.path.join("docs", "tasks", f"TASK-{issue_number}.md")
    if not os.path.exists(task_filename):
        logger.warning(f"Local task file {task_filename} not found")
        print(f"Local task file {task_filename} not found.")
        create_local = input("Would you like to create a local task file? (y/n): ")
        if create_local.lower() == 'y':
            try:
                with open(task_filename, "w") as f:
                    f.write(f"# {task_title}\n\n## Task Details\n- **Issue:** #{issue_number}\n\n## Verification Results\n- {verification}\n")
                logger.info(f"Local task file {task_filename} created")
                print(f"Local task file {task_filename} created.")
            except Exception as e:
                logger.error(f"Failed to create task file: {e}")
                print(f"Error creating task file: {e}")
    else:
        # Append verification results to the file
        try:
            with open(task_filename, "r+") as f:
                content = f.read()
                if "## Verification Results" in content:
                    logger.debug("Verification results section already exists. Adding new entry.")
                    # Position file pointer at the end of the file
                    f.seek(0, 2)
                    f.write(f"- {verification}\n")
                else:
                    f.seek(0, 2)
                    f.write(f"\n## Verification Results\n- {verification}\n")
            logger.info(f"Task file {task_filename} updated with verification results")
            print(f"Task file {task_filename} updated with verification results.")
        except Exception as e:
            logger.error(f"Failed to update task file: {e}")
            print(f"Error updating task file: {e}")

    # Add a comment and close the GitHub issue
    success, message = add_comment_and_close_issue(issue_number, f"Task completed: {verification}", config)
    if success:
        logger.info(f"Successfully added comment and closed GitHub issue #{issue_number}")
        print(f"Successfully added comment and closed GitHub issue #{issue_number}.")
    else:
        logger.error(f"Failed to update or close GitHub issue #{issue_number}: {message}")
        print(f"Failed to update or close GitHub issue #{issue_number}.")
        print(f"Reason: {message}")
        print("Please check the logs for more details.")

if __name__ == "__main__":
    main()
