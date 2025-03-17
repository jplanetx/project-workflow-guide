#!/usr/bin/env python
import sys
import os
import requests
import json
import time
from datetime import datetime
from configparser import ConfigParser
from dotenv import load_dotenv

# Import our custom logger
from task_logger import setup_logger

# Set up logger
logger = setup_logger('start_task')

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
        # Create default config file
        config['github'] = {
            'owner': 'YOUR_GITHUB_USERNAME',
            'repo': 'YOUR_REPO_NAME'
        }
        with open(config_file, 'w') as f:
            config.write(f)
        logger.error(f"Please update GitHub repository details in {config_file}")
        sys.exit(1)
    
    config.read(config_file)
    
    # Combine token from .env with other settings from config.ini
    github_config = {
        'token': github_token,
        'owner': config['github']['owner'],
        'repo': config['github']['repo']
    }
    
    return github_config

def check_duplicate_issues(title, config, max_retries=3):
    """Check if an issue with the same title already exists."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    search_url = f"https://api.github.com/search/issues?q=repo:{config['owner']}/{config['repo']}+is:issue+\"{title}\""
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Checking for duplicate issues with title: {title}")
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            search_results = response.json()
            
            for item in search_results['items']:
                if item['title'].lower() == title.lower():
                    logger.info(f"Found existing issue with the same title: #{item['number']}")
                    return item['number'], item['html_url']
            
            logger.debug("No duplicate issues found")
            return None, None
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed when checking for duplicates: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to check for duplicate issues after {max_retries} attempts")
                return None, None

def create_github_issue(title, config, max_retries=3):
    """Create a GitHub issue using the API with retry logic."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    issue_template = f"""## Task Description
[Add detailed description here]

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Additional Notes
- Created via task automation script
- Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    data = {
        'title': title,
        'body': issue_template,
        'labels': ['Task']
    }
    
    url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues"
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempting to create GitHub issue: {title}")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            issue = response.json()
            logger.info(f"Successfully created GitHub issue #{issue['number']}")
            return issue['number'], issue['html_url']
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to create GitHub issue after {max_retries} attempts")
                return None, None

def main():
    if len(sys.argv) < 2:
        logger.error("Missing required argument: task title")
        print("Usage: start_task.py 'Task Title'")
        sys.exit(1)

    task_title = sys.argv[1]
    logger.info(f"Starting task: {task_title}")
    
    # Load GitHub configuration
    try:
        config = load_config()
        logger.debug("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

    # Check for duplicate issues first
    duplicate_number, duplicate_url = check_duplicate_issues(task_title, config)
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
        # Create GitHub issue if no duplicates found
        issue_number, issue_url = create_github_issue(task_title, config)
    
    if issue_number:
        # Create local task file
        task_filename = os.path.join("docs", "tasks", f"TASK-{issue_number}.md")
        
        task_template = f"""# {task_title}

## Task Details
- **Issue:** #{issue_number}
- **URL:** {issue_url}
- **Created:** {datetime.now().strftime('%Y-%m-%d')}

## Implementation Notes
- Describe your planned approach, key decisions, and any challenges you anticipate.

## Testing Steps
- Outline the steps required to test the implementation.

## Verification Results
- Record the outcomes of your testing and verification checks.
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
    main()
