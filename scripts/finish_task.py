#!/usr/bin/env python
import sys
import os
import json
import glob
import time
import asyncio
import httpx
from datetime import datetime
from configparser import ConfigParser
from dotenv import load_dotenv

# Import our custom logger and AI modules
from task_logger import setup_logger
from token_tracker import TokenTracker
import ai_agents

# Set up logger
logger = setup_logger('finish_task')

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
        logger.error(f"Config file {config_file} does not exist")
        print(f"Config file {config_file} does not exist. Please create it first.")
        return None
    
    config.read(config_file)
    
    # Combine token from .env with other settings from config.ini
    github_config = {
        'token': github_token,
        'owner': config['github']['owner'],
        'repo': config['github']['repo']
    }
    
    return github_config

async def find_issues_by_title(title, config):
    """Find GitHub issues by title with async HTTP."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Search for issues with the given title
    search_url = f"https://api.github.com/search/issues?q=repo:{config['owner']}/{config['repo']}+is:issue+\"{title}\""
    
    async with httpx.AsyncClient() as client:
        for attempt in range(3):  # Max 3 retries
            try:
                logger.debug(f"Searching for issues with title: {title}")
                response = await client.get(search_url, headers=headers)
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
                
            except httpx.HTTPStatusError as e:
                logger.warning(f"Attempt {attempt + 1}/3 failed when searching for issues: {e}")
                if attempt < 2:
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to search for GitHub issues after 3 attempts")
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

async def add_comment_and_close_issue(issue_number, comment, config):
    """Add a comment to an issue and close it with async HTTP."""
    headers = {
        'Authorization': f'token {config["token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # First, check if the issue exists and is open
    issue_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues/{issue_number}"
    
    async with httpx.AsyncClient() as client:
        for attempt in range(3):  # Max 3 retries
            try:
                logger.debug(f"Checking issue #{issue_number} status")
                response = await client.get(issue_url, headers=headers)
                response.raise_for_status()
                issue_data = response.json()
                
                if issue_data['state'] == 'closed':
                    logger.warning(f"Issue #{issue_number} is already closed")
                    return False, "Issue is already closed"
                break
            except httpx.HTTPStatusError as e:
                logger.warning(f"Attempt {attempt + 1}/3 failed when checking issue status: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to check issue status after 3 attempts")
                    return False, f"Failed to check issue status: {e}"
        
        # Add a comment
        comment_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues/{issue_number}/comments"
        comment_data = {
            'body': comment
        }
        
        # Try to add a comment
        for attempt in range(3):  # Max 3 retries
            try:
                logger.debug(f"Adding comment to issue #{issue_number}")
                response = await client.post(comment_url, headers=headers, json=comment_data)
                response.raise_for_status()
                logger.info(f"Comment added to issue #{issue_number}")
                break
            except httpx.HTTPStatusError as e:
                logger.warning(f"Attempt {attempt + 1}/3 failed when adding comment: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to add comment after 3 attempts")
                    return False, f"Failed to add comment: {e}"
        
        # Close the issue
        close_data = {
            'state': 'closed'
        }
        
        # Try to close the issue
        for attempt in range(3):  # Max 3 retries
            try:
                logger.debug(f"Closing issue #{issue_number}")
                response = await client.patch(issue_url, headers=headers, json=close_data)
                response.raise_for_status()
                logger.info(f"Successfully closed issue #{issue_number}")
                return True, "Success"
            except httpx.HTTPStatusError as e:
                logger.warning(f"Attempt {attempt + 1}/3 failed when closing issue: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to close issue after 3 attempts")
                    return False, f"Failed to close issue: {e}"

async def find_task_code_files(task_id):
    """Find code files related to a specific task."""
    # Look for code files in AI output directory
    ai_output_dir = os.path.join("docs", "ai_output")
    if not os.path.exists(ai_output_dir):
        logger.warning(f"AI output directory not found: {ai_output_dir}")
        return []
    
    # Find all files related to this task ID
    task_files = glob.glob(os.path.join(ai_output_dir, f"*{task_id}*"))
    
    # Also search in main code directories
    code_files = []
    for extension in ['py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'json']:
        code_files.extend(glob.glob(f"**/*.{extension}", recursive=True))
    
    # We'll check file contents for task ID references
    related_files = []
    for file_path in code_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check if the file contains mentions of the task ID
                if f"#{task_id}" in content or f"TASK-{task_id}" in content:
                    related_files.append(file_path)
        except Exception as e:
            logger.debug(f"Error reading file {file_path}: {e}")
    
    return task_files + related_files

async def generate_ai_recommendations(task_id, task_title, code_files=None):
    """Generate AI-driven insights and recommendations for completed task."""
    logger.info(f"Generating AI recommendations for task #{task_id}: {task_title}")
    print(f"Generating AI recommendations for task #{task_id}...")
    
    # If we have code files, read their content for analysis
    code_content = ""
    if code_files:
        for file_path in code_files[:3]:  # Limit to first 3 files to avoid token limits
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Add file content with a header
                    code_content += f"\n\n### File: {file_path}\n```\n{content}\n```\n"
            except Exception as e:
                logger.error(f"Error reading code file {file_path}: {e}")
    
    try:
        # Use the executor agent to generate recommendations
        output_dir = os.path.join("docs", "ai_recommendations")
        results = await ai_agents.run_executor_agent(
            task_type="improvement_recommendations",
            task_id=str(task_id),
            task_title=task_title,
            code_input=code_content,
            output_dir=output_dir
        )
        
        if "error" in results:
            logger.error(f"Error generating recommendations: {results['error']}")
            return None
        
        # Return the files that were saved
        recommendation_files = results.get("saved_files", [])
        logger.info(f"Generated recommendations saved to {output_dir}")
        return recommendation_files
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {e}")
        return None

async def update_ai_recommendations_index(new_files=None):
    """Update the AI recommendations index file with links to all recommendations."""
    recommendations_dir = os.path.join("docs", "ai_recommendations")
    index_file = os.path.join(recommendations_dir, "README.md")
    
    # Create directory if it doesn't exist
    os.makedirs(recommendations_dir, exist_ok=True)
    
    # Find all markdown files in the recommendations directory
    md_files = glob.glob(os.path.join(recommendations_dir, "*.md"))
    md_files = [f for f in md_files if os.path.basename(f) != "README.md"]
    
    # Create content for the index file
    content = "# AI-Generated Insights and Recommendations\n\n"
    content += "This directory contains AI-generated insights and recommendations for completed tasks.\n\n"
    content += "## Available Recommendations\n\n"
    
    if md_files:
        for file_path in sorted(md_files, key=os.path.getmtime, reverse=True):
            file_name = os.path.basename(file_path)
            # Extract task ID from filename (improvements_123.md -> 123)
            task_id = file_name.replace("improvements_", "").replace(".md", "")
            
            # Try to extract the title from the file
            title = f"Task #{task_id}"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith("# "):
                        title = first_line[2:]
            except Exception:
                pass
            
            content += f"- [{title}]({file_name})\n"
    else:
        content += "*No recommendations available yet.*\n"
    
    # Add information about newly added files
    if new_files:
        content += "\n## Recently Added\n\n"
        for file_path in new_files:
            if file_path.endswith(".md"):
                file_name = os.path.basename(file_path)
                content += f"- [{file_name}]({file_name})\n"
    
    # Add footer
    content += "\n\n---\n*Last updated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*\n"
    
    # Write the index file
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Updated AI recommendations index at {index_file}")
        return index_file
    except Exception as e:
        logger.error(f"Error updating AI recommendations index: {e}")
        return None

async def main():
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
    config = await load_config()
    if not config:
        logger.error("Failed to load configuration")
        sys.exit(1)
    
    logger.debug("Configuration loaded successfully")

    # Try to find issue number from local files first
    issue_number = find_issue_from_local_files(task_title)
    
    # If not found in local files, search GitHub by title
    if not issue_number:
        logger.info("Issue not found in local files, searching GitHub by title")
        matching_issues = await find_issues_by_title(task_title, config)
        
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
    
    # Find code files associated with the task
    code_files = await find_task_code_files(issue_number)
    if code_files:
        logger.info(f"Found {len(code_files)} code files related to task #{issue_number}")
        print(f"Found {len(code_files)} code files associated with this task.")
    
    # Generate AI insights and recommendations
    print("Generating AI insights and recommendations...")
    recommendation_files = await generate_ai_recommendations(issue_number, task_title, code_files)
    
    if recommendation_files:
        # Update the recommendations index
        index_file = await update_ai_recommendations_index(recommendation_files)
        if index_file:
            print(f"AI recommendations generated and saved to {os.path.dirname(index_file)}")
            
            # Construct link to recommendations for GitHub comment
            rec_file = [f for f in recommendation_files if f.endswith('.md')]
            rec_file_rel_path = None
            if rec_file:
                rec_file_rel_path = os.path.join("docs", "ai_recommendations", os.path.basename(rec_file[0]))
    else:
        print("Note: Could not generate AI recommendations.")
        rec_file_rel_path = None
    
    # Prepare the closing comment
    comment = f"Task completed: {verification}"
    if rec_file_rel_path:
        comment += f"\n\n**AI-Generated Insights:** AI has analyzed this task and generated improvement recommendations. See {rec_file_rel_path} for details."
    
    # Add a comment and close the GitHub issue
    success, message = await add_comment_and_close_issue(issue_number, comment, config)
    if success:
        logger.info(f"Successfully added comment and closed GitHub issue #{issue_number}")
        print(f"Successfully added comment and closed GitHub issue #{issue_number}.")
    else:
        logger.error(f"Failed to update or close GitHub issue #{issue_number}: {message}")
        print(f"Failed to update or close GitHub issue #{issue_number}.")
        print(f"Reason: {message}")
        print("Please check the logs for more details.")

if __name__ == "__main__":
    asyncio.run(main())