#!/usr/bin/env python
import sys
import os
import requests
import json
from datetime import datetime
from configparser import ConfigParser

def load_config():
    config = ConfigParser()
    config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    if not os.path.exists(config_file):
        # Create default config file
        config['github'] = {
            'token': 'YOUR_GITHUB_TOKEN',
            'owner': 'YOUR_GITHUB_USERNAME',
            'repo': 'YOUR_REPO_NAME'
        }
        with open(config_file, 'w') as f:
            config.write(f)
        print(f"Please update GitHub credentials in {config_file}")
        sys.exit(1)
    
    config.read(config_file)
    return config['github']

def create_github_issue(title, config):
    """Create a GitHub issue using the API."""
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
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        issue = response.json()
        return issue['number'], issue['html_url']
    except requests.exceptions.RequestException as e:
        print(f"Error creating GitHub issue: {e}")
        return None, None

def main():
    if len(sys.argv) < 2:
        print("Usage: start_task.py 'Task Title'")
        sys.exit(1)

    task_title = sys.argv[1]
    
    # Load GitHub configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Create GitHub issue
    issue_number, issue_url = create_github_issue(task_title, config)
    
    if issue_number:
        print(f"GitHub issue #{issue_number} created successfully")
        print(f"Issue URL: {issue_url}")
        
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
        os.makedirs(os.path.dirname(task_filename), exist_ok=True)
        with open(task_filename, "w") as f:
            f.write(task_template)
        print(f"Task file {task_filename} created successfully.")
    else:
        print("Failed to create GitHub issue. Please check your configuration and try again.")

if __name__ == "__main__":
    main()
