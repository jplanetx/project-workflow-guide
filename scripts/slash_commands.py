#!/usr/bin/env python
import os
import sys
import json
import asyncio
import argparse
import httpx
from datetime import datetime
from configparser import ConfigParser
from dotenv import load_dotenv

# Import custom modules
from task_logger import setup_logger
from token_tracker import TokenTracker
from ai_agents import BaseAgent, CollectorAgent, ExecutorAgent, load_config_async

# Set up logger
logger = setup_logger('slash_commands')
token_tracker = TokenTracker()

class SlashCommandsAgent(BaseAgent):
    """Agent for handling slash commands with AI integration"""
    
    def __init__(self, config, brief_mode=False):
        super().__init__(config)
        self.brief_mode = brief_mode
        
    async def fetch_unresolved_issues(self):
        """Fetch all unresolved GitHub issues (/check-bugs command)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"https://api.github.com/repos/{self.config['owner']}/{self.config['repo']}/issues?state=open"
            try:
                response = await client.get(url, headers=self.headers)
                
                if await self.handle_rate_limit(response):
                    return await self.fetch_unresolved_issues()  # Retry after rate limit reset
                
                response.raise_for_status()
                issues = response.json()
                
                # Filter out pull requests and extract relevant info
                bug_issues = []
                for issue in issues:
                    # Skip pull requests
                    if 'pull_request' in issue:
                        continue
                        
                    # Check if issue has bug label
                    labels = [label['name'].lower() for label in issue['labels']]
                    is_bug = any(label in ['bug', 'defect', 'error', 'fix'] for label in labels)
                    
                    bug_issues.append({
                        'number': issue['number'],
                        'title': issue['title'],
                        'created_at': issue['created_at'],
                        'updated_at': issue['updated_at'],
                        'url': issue['html_url'],
                        'is_bug': is_bug,
                        'labels': [label['name'] for label in issue['labels']]
                    })
                
                logger.info(f"Successfully fetched {len(bug_issues)} open issues")
                return bug_issues
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching issues: {e}")
                return []
    
    async def summarize_readme(self):
        """Summarize the repository README (/summarize-docs command)"""
        # First, fetch the README content
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"https://api.github.com/repos/{self.config['owner']}/{self.config['repo']}/readme"
            try:
                response = await client.get(url, headers=self.headers)
                
                if await self.handle_rate_limit(response):
                    return await self.summarize_readme()  # Retry after rate limit reset
                
                response.raise_for_status()
                readme_data = response.json()
                
                # GitHub returns README content as base64 encoded
                import base64
                readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
                logger.info("Successfully fetched README.md")
                
                # For brevity in token usage, trim the readme if it's very long
                if len(readme_content) > 10000 and self.brief_mode:
                    logger.info("Trimming README content for efficiency")
                    readme_content = readme_content[:10000] + "..."
                
                # Generate the summary using an AI call
                summary = await self.generate_readme_summary(readme_content)
                return {
                    "original_length": len(readme_content),
                    "summary": summary
                }
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching README: {e}")
                return {"error": f"Could not fetch README: {e}"}
    
    async def generate_tests(self):
        """Generate tests for recent code changes (/generate-tests command)"""
        # First, get recent commits to find files that changed
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"https://api.github.com/repos/{self.config['owner']}/{self.config['repo']}/commits?per_page=3"
            try:
                response = await client.get(url, headers=self.headers)
                
                if await self.handle_rate_limit(response):
                    return await self.generate_tests()  # Retry after rate limit reset
                
                response.raise_for_status()
                commits = response.json()
                
                # Get the most recent commit sha
                recent_commit_sha = commits[0]['sha']
                
                # Get the files changed in this commit
                url = f"https://api.github.com/repos/{self.config['owner']}/{self.config['repo']}/commits/{recent_commit_sha}"
                response = await client.get(url, headers=self.headers)
                
                if await self.handle_rate_limit(response):
                    return await self.generate_tests()  # Retry after rate limit reset
                
                response.raise_for_status()
                commit_data = response.json()
                
                # Extract Python files that were changed
                python_files = [file for file in commit_data['files'] if file['filename'].endswith('.py')]
                
                if not python_files:
                    return {"error": "No Python files were changed in the recent commit"}
                
                # For each file, get the content and generate tests
                test_results = []
                for file_info in python_files[:2]:  # Limit to first 2 files for efficiency
                    file_path = file_info['filename']
                    
                    # Get the file content
                    try:
                        url = f"https://raw.githubusercontent.com/{self.config['owner']}/{self.config['repo']}/main/{file_path}"
                        response = await client.get(url)
                        response.raise_for_status()
                        file_content = response.text
                        
                        # Generate tests for this file
                        tests = await self.generate_file_tests(file_path, file_content)
                        test_results.append({
                            "file_path": file_path,
                            "tests": tests
                        })
                    except Exception as e:
                        logger.error(f"Error getting content for {file_path}: {e}")
                
                return {
                    "commit_sha": recent_commit_sha,
                    "test_results": test_results
                }
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Error generating tests: {e}")
                return {"error": f"Error generating tests: {e}"}
    
    async def generate_readme_summary(self, readme_content):
        """Generate a summary of the README using AI"""
        # This is where an actual AI call would happen
        # For now, we'll simulate it and track tokens
        logger.info("Generating README summary")
        
        # Simulate AI processing time
        await asyncio.sleep(0.5)
        
        # Calculate token usage (estimate)
        prompt_tokens = len(readme_content) // 4
        completion_tokens = 300 if self.brief_mode else 800
        
        # Log token usage
        self.log_token_usage(
            api_name="claude-3-sonnet",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            notes="README summary generation"
        )
        
        # For now, just return a simple summary based on the first section
        # In a real implementation, this would call Claude or another AI
        if "Project Workflow Guide" in readme_content:
            summary = {
                "title": "Project Workflow Guide",
                "description": "A repository that provides templates and guidelines for project workflow with GitHub integration.",
                "key_features": [
                    "GitHub Integration for issue and PR management",
                    "Local task management with markdown files",
                    "Standardized templates for consistent workflow",
                    "Built-in error handling and logging"
                ],
                "setup_steps": [
                    "Clone the repository",
                    "Configure GitHub integration",
                    "Install dependencies",
                    "Start using the workflow scripts"
                ]
            }
        else:
            # Generic fallback if it's not the sample README
            lines = readme_content.split('\n')
            title = next((line for line in lines if line.startswith('# ')), "").replace('# ', '')
            
            summary = {
                "title": title or "Repository Documentation",
                "description": "This repository contains project documentation and workflow tools.",
                "sections": [section for section in readme_content.split('##') if section.strip()][:3]
            }
        
        return summary
    
    async def generate_file_tests(self, file_path, file_content):
        """Generate tests for a Python file using AI"""
        # This is where an actual AI call would happen
        # For now, we'll simulate it and track tokens
        logger.info(f"Generating tests for {file_path}")
        
        # Simulate AI processing time
        await asyncio.sleep(0.7)
        
        # Calculate token usage (estimate)
        prompt_tokens = len(file_content) // 4
        completion_tokens = 500 if self.brief_mode else 1200
        
        # Log token usage
        self.log_token_usage(
            api_name="claude-3-sonnet",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            notes=f"Test generation for {file_path}"
        )
        
        # Extract file name without extension for test class name
        file_name = os.path.basename(file_path).replace('.py', '')
        class_name = ''.join(word.capitalize() for word in file_name.split('_'))
        
        # Generate mock tests based on imported modules and function definitions
        import re
        
        # Find imports
        imports = re.findall(r'^import (\w+)|^from (\w+) import', file_content, re.MULTILINE)
        imports = [imp[0] or imp[1] for imp in imports if imp[0] or imp[1]]
        
        # Find functions
        functions = re.findall(r'def (\w+)\s*\(', file_content)
        
        # Generate mock test content
        test_content = f"""import unittest
from unittest.mock import patch, MagicMock
import {file_name}

class Test{class_name}(unittest.TestCase):
    def setUp(self):
        # Setup test environment
        self.test_data = {{}}
"""

        for func in functions:
            test_content += f"""
    def test_{func}(self):
        # Test the {func} function
        result = {file_name}.{func}()
        self.assertIsNotNone(result)
"""

        test_content += """
if __name__ == '__main__':
    unittest.main()
"""
        
        return test_content
        
    def format_issues_report(self, issues):
        """Format the issues list as Markdown"""
        if not issues:
            return "## Bug Check Report\n\nNo open issues found."
        
        report = "## Bug Check Report\n\n"
        report += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # Group by whether they're labeled as bugs
        bugs = [issue for issue in issues if issue['is_bug']]
        other_issues = [issue for issue in issues if not issue['is_bug']]
        
        if bugs:
            report += "### Bugs\n\n"
            for bug in bugs:
                labels = f" ({', '.join(bug['labels'])})" if bug['labels'] else ""
                report += f"- #{bug['number']} [{bug['title']}]({bug['url']}){labels}\n"
            report += "\n"
        
        if other_issues and not self.brief_mode:
            report += "### Other Issues\n\n"
            for issue in other_issues:
                labels = f" ({', '.join(issue['labels'])})" if issue['labels'] else ""
                report += f"- #{issue['number']} [{issue['title']}]({issue['url']}){labels}\n"
        
        report += f"\nTotal bugs: {len(bugs)}\n"
        report += f"Total other issues: {len(other_issues)}\n"
        
        return report
    
    def format_readme_summary(self, summary_data):
        """Format the README summary as Markdown"""
        if "error" in summary_data:
            return f"## README Summary\n\nError: {summary_data['error']}"
        
        summary = summary_data['summary']
        report = "## README Summary\n\n"
        report += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        if "title" in summary:
            report += f"### {summary['title']}\n\n"
        
        if "description" in summary:
            report += f"{summary['description']}\n\n"
        
        if "key_features" in summary:
            report += "### Key Features\n\n"
            for feature in summary['key_features']:
                report += f"- {feature}\n"
            report += "\n"
        
        if "setup_steps" in summary:
            report += "### Setup\n\n"
            for i, step in enumerate(summary['setup_steps'], 1):
                report += f"{i}. {step}\n"
            report += "\n"
        
        if "sections" in summary and not self.brief_mode:
            report += "### Main Sections\n\n"
            for section in summary['sections'][:3]:  # First 3 sections
                section_title = section.split('\n')[0].strip()
                report += f"- {section_title}\n"
        
        report += f"\nSummarized from {summary_data['original_length']} characters."
        
        return report
    
    def format_test_report(self, test_data):
        """Format the test generation results as Markdown"""
        if "error" in test_data:
            return f"## Test Generation Report\n\nError: {test_data['error']}"
        
        report = "## Test Generation Report\n\n"
        report += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        report += f"Generated tests for commit: `{test_data['commit_sha'][:7]}`\n\n"
        
        for result in test_data['test_results']:
            file_path = result['file_path']
            tests = result['tests']
            
            report += f"### Tests for `{file_path}`\n\n"
            
            if self.brief_mode:
                # In brief mode, just show a summary
                test_lines = tests.count('\n')
                test_functions = tests.count('def test_')
                report += f"Generated {test_functions} test functions ({test_lines} lines).\n\n"
            else:
                # In full mode, include the test code
                report += "```python\n"
                report += tests
                report += "\n```\n\n"
        
        return report
    
    async def run(self, command, args=None):
        """Run the specified slash command"""
        if command == "/check-bugs":
            issues = await self.fetch_unresolved_issues()
            return self.format_issues_report(issues)
            
        elif command == "/summarize-docs":
            summary_data = await self.summarize_readme()
            return self.format_readme_summary(summary_data)
            
        elif command == "/generate-tests":
            test_data = await self.generate_tests()
            return self.format_test_report(test_data)
            
        else:
            return f"Unknown command: {command}\n\nAvailable commands:\n- /check-bugs\n- /summarize-docs\n- /generate-tests"


async def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description="AI-powered slash commands for development workflow")
    parser.add_argument("command", help="The slash command to run (/check-bugs, /summarize-docs, /generate-tests)")
    parser.add_argument("--brief_mode", action="store_true", help="Enable brief mode to reduce token consumption")
    parser.add_argument("--output", "-o", help="Output file path for the report (defaults to stdout)")
    
    args = parser.parse_args()
    
    # Make sure the command starts with /
    command = args.command if args.command.startswith('/') else f"/{args.command}"
    
    # Load configuration
    config = await load_config_async()
    if not config:
        logger.error("Failed to load configuration")
        print("Error: Failed to load GitHub configuration. Make sure your .env and config.ini files are set up correctly.")
        sys.exit(1)
    
    # Create and run the slash command agent
    agent = SlashCommandsAgent(config, brief_mode=args.brief_mode)
    result = await agent.run(command)
    
    # Output the result
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Report saved to {args.output}")
        except Exception as e:
            logger.error(f"Error saving output to {args.output}: {e}")
            print(f"Error: Could not save to {args.output}. {e}")
            print(result)
    else:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())