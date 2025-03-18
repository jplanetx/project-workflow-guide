#!/usr/bin/env python
import os
import sys
import json
import asyncio
import httpx
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from configparser import ConfigParser
from dotenv import load_dotenv

# Import custom modules
from task_logger import setup_logger
from token_tracker import TokenTracker

# Set up logger
logger = setup_logger('ai_agents')
token_tracker = TokenTracker()

class BaseAgent:
    """Base class for all AI agents"""
    
    def __init__(self, config: Dict[str, Any], task_id: Optional[str] = None, task_title: Optional[str] = None):
        self.config = config
        self.task_id = task_id
        self.task_title = task_title
        self.headers = {
            'Authorization': f'token {config["token"]}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.results = {}
        self.timeout = httpx.Timeout(30.0)
    
    async def run(self) -> Dict[str, Any]:
        """Run the agent's tasks - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement run()")
    
    def log_token_usage(self, api_name: str, prompt_tokens: int, completion_tokens: int, notes: str = ""):
        """Log token usage for tracking"""
        task_id = self.task_id or "general"
        task_title = self.task_title or "General Agent Task"
        
        token_tracker.log_token_usage(
            task_id=task_id,
            task_title=task_title,
            api_name=api_name,
            endpoint="completion",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            notes=notes
        )
    
    async def handle_rate_limit(self, response: httpx.Response) -> bool:
        """Handle GitHub API rate limiting"""
        if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
            remaining = int(response.headers['X-RateLimit-Remaining'])
            if remaining == 0:
                reset_time = int(response.headers['X-RateLimit-Reset'])
                current_time = time.time()
                sleep_time = reset_time - current_time + 1
                if sleep_time > 0:
                    logger.warning(f"Rate limit exceeded. Waiting for {sleep_time:.2f} seconds")
                    await asyncio.sleep(sleep_time)
                    return True
        return False


class CollectorAgent(BaseAgent):
    """Agent responsible for collecting and organizing relevant project data"""
    
    async def get_readme(self) -> str:
        """Fetch the repository README content"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"https://api.github.com/repos/{self.config['owner']}/{self.config['repo']}/readme"
            try:
                response = await client.get(url, headers=self.headers)
                
                if await self.handle_rate_limit(response):
                    return await self.get_readme()  # Retry after rate limit reset
                
                response.raise_for_status()
                readme_data = response.json()
                
                # GitHub returns README content as base64 encoded
                import base64
                readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
                logger.info("Successfully fetched README.md")
                return readme_content
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching README: {e}")
                return "README content unavailable"
    
    async def get_recent_commits(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent commits from the repository"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"https://api.github.com/repos/{self.config['owner']}/{self.config['repo']}/commits?per_page={limit}"
            try:
                response = await client.get(url, headers=self.headers)
                
                if await self.handle_rate_limit(response):
                    return await self.get_recent_commits(limit)  # Retry after rate limit reset
                
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
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching commits: {e}")
                return []
    
    async def get_issues(self, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch issues from the repository"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"https://api.github.com/repos/{self.config['owner']}/{self.config['repo']}/issues?state={state}&per_page={limit}"
            try:
                response = await client.get(url, headers=self.headers)
                
                if await self.handle_rate_limit(response):
                    return await self.get_issues(state, limit)  # Retry after rate limit reset
                
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
                
                logger.info(f"Successfully fetched {len(issue_summaries)} {state} issues")
                return issue_summaries
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching issues: {e}")
                return []
    
    async def get_error_logs(self, logs_dir: str = None) -> Dict[str, str]:
        """Fetch recent error logs from the logs directory"""
        if logs_dir is None:
            logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        
        log_snippets = {}
        try:
            # Get a list of log files, sorted by modification time (newest first)
            log_files = []
            for root, _, files in os.walk(logs_dir):
                for file in files:
                    if file.endswith('.log'):
                        full_path = os.path.join(root, file)
                        log_files.append((full_path, os.path.getmtime(full_path)))
            
            # Sort by modification time, newest first
            log_files.sort(key=lambda x: x[1], reverse=True)
            
            # Extract error lines from the most recent logs (limit to 5 files)
            for log_path, _ in log_files[:5]:
                log_name = os.path.basename(log_path)
                error_lines = []
                
                with open(log_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'ERROR' in line or 'CRITICAL' in line:
                            error_lines.append(line.strip())
                
                # Only include logs with errors, limited to most recent 10 errors
                if error_lines:
                    log_snippets[log_name] = '\n'.join(error_lines[-10:])
            
            logger.info(f"Collected error logs from {len(log_snippets)} files")
            return log_snippets
            
        except Exception as e:
            logger.error(f"Error collecting log files: {e}")
            return {"error": str(e)}
    
    async def get_project_structure(self, max_depth: int = 3) -> Dict[str, Any]:
        """Get the directory structure of the project"""
        root_dir = os.path.join(os.path.dirname(__file__), '..')
        root_dir = os.path.abspath(root_dir)
        
        def generate_structure(directory, depth=0):
            if depth > max_depth:
                return "..."
            
            structure = {}
            try:
                for item in os.listdir(directory):
                    # Skip hidden files and directories
                    if item.startswith('.'):
                        continue
                        
                    full_path = os.path.join(directory, item)
                    if os.path.isdir(full_path):
                        # For directories, recursively explore
                        structure[item + '/'] = generate_structure(full_path, depth + 1)
                    else:
                        # For files, just note the name
                        structure[item] = None
            except Exception as e:
                logger.error(f"Error accessing directory {directory}: {e}")
                return {"error": str(e)}
            
            return structure
        
        logger.debug("Generating project directory structure")
        directory_structure = generate_structure(root_dir)
        logger.info("Successfully generated directory structure")
        return directory_structure
    
    async def run(self) -> Dict[str, Any]:
        """Run all data collection tasks in parallel"""
        tasks = [
            self.get_readme(),
            self.get_recent_commits(),
            self.get_issues("open"),
            self.get_issues("closed", 5),
            self.get_error_logs(),
            self.get_project_structure()
        ]
        
        logger.info("Starting parallel data collection")
        results = await asyncio.gather(*tasks)
        
        # Organize the results
        self.results = {
            "readme": results[0],
            "recent_commits": results[1],
            "open_issues": results[2],
            "closed_issues": results[3],
            "error_logs": results[4],
            "project_structure": results[5],
            "collected_at": datetime.now().isoformat(),
        }
        
        # Calculate approximate token count for this context
        # (rough estimate based on characters)
        readme_tokens = len(str(self.results["readme"])) // 4
        commits_tokens = len(str(self.results["recent_commits"])) // 4
        issues_tokens = (len(str(self.results["open_issues"])) + 
                         len(str(self.results["closed_issues"]))) // 4
        logs_tokens = len(str(self.results["error_logs"])) // 4
        structure_tokens = len(str(self.results["project_structure"])) // 4
        
        total_tokens = readme_tokens + commits_tokens + issues_tokens + logs_tokens + structure_tokens
        
        # Log token usage for context collection
        self.log_token_usage(
            api_name="internal_collection",
            prompt_tokens=total_tokens,
            completion_tokens=0,
            notes="Context collection for task preparation"
        )
        
        logger.info(f"Completed data collection (est. {total_tokens} tokens)")
        return self.results
    
    def generate_context_document(self, output_path: str = None) -> str:
        """Generate a markdown document from the collected context"""
        if not self.results:
            logger.error("No results available. Run the agent first.")
            return ""
        
        context_md = "# AI Context Primer\n\n"
        context_md += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # Add task-specific information if a title was provided
        if self.task_title:
            context_md += f"## Current Task: {self.task_title}\n\n"
            if self.task_id:
                context_md += f"Task ID: {self.task_id}\n\n"
        
        # Add README content
        context_md += "## Project Overview\n\n"
        context_md += self.results["readme"] + "\n\n"
        
        # Add recent commit history
        context_md += "## Recent Commits\n\n"
        for commit in self.results["recent_commits"]:
            context_md += f"- [{commit['sha']}] {commit['message']} - *{commit['author']}* on {commit['date'].split('T')[0]}\n"
        context_md += "\n"
        
        # Add issues
        context_md += "## Open Issues\n\n"
        for issue in self.results["open_issues"]:
            labels_str = ", ".join([f"`{label}`" for label in issue['labels']]) if issue['labels'] else ""
            context_md += f"- #{issue['number']} [{issue['title']}]({issue['url']}) {labels_str}\n"
        context_md += "\n"
        
        context_md += "## Recently Closed Issues\n\n"
        for issue in self.results["closed_issues"]:
            labels_str = ", ".join([f"`{label}`" for label in issue['labels']]) if issue['labels'] else ""
            context_md += f"- #{issue['number']} [{issue['title']}]({issue['url']}) {labels_str}\n"
        context_md += "\n"
        
        # Add error logs if any
        if self.results["error_logs"]:
            context_md += "## Recent Errors\n\n"
            for log_file, errors in self.results["error_logs"].items():
                context_md += f"### {log_file}\n\n```\n{errors}\n```\n\n"
        
        # Add project structure
        context_md += "## Project Structure\n\n```\n"
        context_md += json.dumps(self.results["project_structure"], indent=2)
        context_md += "\n```\n"
        
        # Save to file if output path is provided
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(context_md)
                logger.info(f"Context document saved to {output_path}")
            except Exception as e:
                logger.error(f"Error saving context document: {e}")
        
        return context_md


class ExecutorAgent(BaseAgent):
    """Agent responsible for executing AI coding tasks and generating code artifacts"""
    
    def __init__(self, config: Dict[str, Any], task_id: Optional[str] = None, task_title: Optional[str] = None, 
                 model: str = "default", context: Optional[Dict[str, Any]] = None):
        super().__init__(config, task_id, task_title)
        self.model = model
        self.context = context or {}
        self.ai_results = {}
    
    async def generate_code(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate code using an AI model (stub for external API integration)"""
        # This would be replaced with actual AI API call in production
        logger.info(f"Generating code for prompt of length {len(prompt)} chars")
        
        # Simulate AI processing time
        await asyncio.sleep(1)
        
        # Estimate token counts
        prompt_tokens = len(prompt) // 4
        completion_tokens = max_tokens // 2  # Simulate a response of ~half the max tokens
        
        # Log token usage
        self.log_token_usage(
            api_name=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            notes=f"Code generation for {self.task_title or 'unknown task'}"
        )
        
        # Mock code generation - in a real implementation, this would call an AI API
        lines = []
        if "function" in prompt.lower() or "class" in prompt.lower():
            # Mock code creation
            func_name = self.task_title.lower().replace(" ", "_") if self.task_title else "sample_function"
            lines = [
                f"def {func_name}(params):",
                "    \"\"\"",
                f"    Implementation for: {self.task_title}",
                "    ",
                "    Generated by AI assistant based on task requirements",
                "    \"\"\"",
                "    # TODO: Implement functionality",
                "    result = None",
                "    ",
                "    # Process input parameters",
                "    if params:",
                "        result = params",
                "    ",
                "    return result"
            ]
        else:
            lines = [
                "# Generated code stub",
                f"# Task: {self.task_title}",
                "# TODO: Replace with actual implementation",
                "",
                "# Import required modules",
                "import os",
                "import sys",
                "",
                "# Main functionality",
                "def main():",
                "    print('Implementing task: {self.task_title}')",
                "    # TODO: Implement main functionality",
                "",
                "if __name__ == '__main__':",
                "    main()"
            ]
        
        generated_code = "\n".join(lines)
        logger.info(f"Generated {len(lines)} lines of code")
        return generated_code
    
    async def generate_tests(self, code: str, max_tokens: int = 1000) -> str:
        """Generate unit tests for the given code"""
        logger.info(f"Generating tests for code of length {len(code)} chars")
        
        # Simulate AI processing time
        await asyncio.sleep(0.5)
        
        # Estimate token counts
        prompt_tokens = len(code) // 4
        completion_tokens = max_tokens // 2  # Simulate a response of ~half the max tokens
        
        # Log token usage
        self.log_token_usage(
            api_name=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            notes=f"Test generation for {self.task_title or 'unknown task'}"
        )
        
        # Extract function/class name for test generation
        import re
        func_match = re.search(r"def\s+(\w+)\s*\(", code)
        class_match = re.search(r"class\s+(\w+)\s*", code)
        
        name = None
        if func_match:
            name = func_match.group(1)
        elif class_match:
            name = class_match.group(1)
        else:
            name = self.task_title.lower().replace(" ", "_") if self.task_title else "sample_function"
        
        # Mock test generation
        lines = [
            "import unittest",
            f"from module import {name}",
            "",
            f"class Test{name.capitalize()}(unittest.TestCase):",
            "    def setUp(self):",
            "        # Set up test fixtures",
            "        self.test_data = {'key': 'value'}",
            "",
            "    def test_basic_functionality(self):",
            f"        # Test that {name} functions correctly with valid input",
            f"        result = {name}(self.test_data)",
            "        self.assertIsNotNone(result)",
            "",
            "    def test_edge_cases(self):",
            f"        # Test that {name} handles edge cases correctly",
            f"        result = {name}(None)",
            "        self.assertIsNone(result)",
            "",
            "if __name__ == '__main__':",
            "    unittest.main()"
        ]
        
        generated_tests = "\n".join(lines)
        logger.info(f"Generated {len(lines)} lines of tests")
        return generated_tests
    
    async def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze code for quality, performance, and security issues"""
        logger.info(f"Analyzing code of length {len(code)} chars")
        
        # Simulate AI processing time
        await asyncio.sleep(0.7)
        
        # Estimate token counts
        prompt_tokens = len(code) // 4
        completion_tokens = 500  # Fixed size for analysis results
        
        # Log token usage
        self.log_token_usage(
            api_name=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            notes=f"Code analysis for {self.task_title or 'unknown task'}"
        )
        
        # Mock code analysis
        analysis = {
            "quality": {
                "score": 0.85,
                "issues": [
                    {"type": "style", "description": "Consider adding more comprehensive docstrings"},
                    {"type": "structure", "description": "Function could be broken down into smaller units"}
                ],
                "strengths": [
                    "Good variable naming",
                    "Clear control flow"
                ]
            },
            "performance": {
                "score": 0.9,
                "issues": [],
                "suggestions": [
                    "Consider caching results for repeated operations"
                ]
            },
            "security": {
                "score": 0.95,
                "vulnerabilities": [],
                "notes": [
                    "Ensure input validation in production environment"
                ]
            }
        }
        
        logger.info("Completed code analysis")
        return analysis
    
    async def generate_improvements(self, task_id: str, task_title: str, code: str = None) -> Dict[str, Any]:
        """Generate improvement recommendations for a completed task"""
        logger.info(f"Generating improvements for task #{task_id}: {task_title}")
        
        # If no code is provided, we'll generate generic recommendations
        if not code:
            code = "# No code provided for analysis"
        
        # Simulate AI processing time
        await asyncio.sleep(1.5)
        
        # Estimate token counts
        context_tokens = sum(len(str(v)) // 4 for v in self.context.values()) if self.context else 0
        prompt_tokens = (len(code) // 4) + context_tokens + 200  # Add extra for task info
        completion_tokens = 1200  # Fixed size for recommendations
        
        # Log token usage
        self.log_token_usage(
            api_name=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            notes=f"Improvement recommendations for task #{task_id}"
        )
        
        # Mock improvement recommendations
        improvements = {
            "technical_debt": [
                "Consider adding comprehensive error handling",
                "Implement proper logging throughout the code",
                "Add type hints for better code documentation"
            ],
            "future_enhancements": [
                "Add support for async operations",
                "Implement caching for frequently accessed data",
                f"Create additional helper functions for {task_title.lower()} operations"
            ],
            "automation_opportunities": [
                "Test generation could be automated for this type of functionality",
                "Consider creating a template for similar features in the future",
                "Automate validation checks for input parameters"
            ],
            "learning_opportunities": [
                "Explore design patterns that could improve this implementation",
                "Consider researching more efficient algorithms for this task type",
                "Review similar implementations in other popular libraries"
            ]
        }
        
        logger.info("Completed generating improvement recommendations")
        return improvements
    
    async def run(self, task_type: str = "code_generation", code_input: str = None) -> Dict[str, Any]:
        """Run the agent with the specified task type"""
        logger.info(f"Running executor agent for task type: {task_type}")
        
        if task_type == "code_generation":
            # Prepare prompt from context
            prompt = f"Generate code for task: {self.task_title}\n\n"
            if self.context:
                prompt += "Context:\n"
                if "readme" in self.context:
                    prompt += f"README snippet: {self.context['readme'][:300]}...\n\n"
                if "open_issues" in self.context and self.context["open_issues"]:
                    prompt += f"Related issues: {', '.join([f'#{i['number']}' for i in self.context['open_issues'][:3]])}\n\n"
            
            # Run code generation tasks in parallel
            generated_code = await self.generate_code(prompt)
            tests = await self.generate_tests(generated_code)
            analysis = await self.analyze_code(generated_code)
            
            self.ai_results = {
                "task_type": "code_generation",
                "task_id": self.task_id,
                "task_title": self.task_title,
                "generated_code": generated_code,
                "generated_tests": tests,
                "code_analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        elif task_type == "improvement_recommendations":
            if not self.task_id or not self.task_title:
                logger.error("Task ID and title are required for improvement recommendations")
                return {"error": "Task ID and title are required"}
            
            improvements = await self.generate_improvements(self.task_id, self.task_title, code_input)
            
            self.ai_results = {
                "task_type": "improvement_recommendations",
                "task_id": self.task_id,
                "task_title": self.task_title,
                "improvements": improvements,
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            logger.error(f"Unknown task type: {task_type}")
            return {"error": f"Unknown task type: {task_type}"}
        
        logger.info(f"Executor agent completed {task_type} task")
        return self.ai_results
    
    def save_results(self, output_dir: str) -> List[str]:
        """Save the AI results to output files"""
        if not self.ai_results:
            logger.error("No results available. Run the agent first.")
            return []
        
        os.makedirs(output_dir, exist_ok=True)
        saved_files = []
        
        if self.ai_results.get("task_type") == "code_generation":
            # Save generated code
            code_file = os.path.join(output_dir, f"generated_code_{self.task_id}.py")
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(self.ai_results["generated_code"])
            saved_files.append(code_file)
            
            # Save generated tests
            test_file = os.path.join(output_dir, f"test_{self.task_id}.py")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(self.ai_results["generated_tests"])
            saved_files.append(test_file)
            
            # Save analysis
            analysis_file = os.path.join(output_dir, f"analysis_{self.task_id}.json")
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(self.ai_results["code_analysis"], f, indent=2)
            saved_files.append(analysis_file)
            
        elif self.ai_results.get("task_type") == "improvement_recommendations":
            # Save recommendations to markdown file
            recommendations_file = os.path.join(output_dir, f"improvements_{self.task_id}.md")
            
            with open(recommendations_file, 'w', encoding='utf-8') as f:
                f.write(f"# Improvement Recommendations for Task #{self.task_id}: {self.task_title}\n\n")
                f.write(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                
                for category, items in self.ai_results["improvements"].items():
                    f.write(f"## {category.replace('_', ' ').title()}\n\n")
                    for item in items:
                        f.write(f"- {item}\n")
                    f.write("\n")
            
            saved_files.append(recommendations_file)
            
            # Also save JSON version
            json_file = os.path.join(output_dir, f"improvements_{self.task_id}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.ai_results["improvements"], f, indent=2)
            saved_files.append(json_file)
        
        logger.info(f"Saved {len(saved_files)} result files to {output_dir}")
        return saved_files


async def load_config_async():
    """Load GitHub configuration asynchronously"""
    # Load environment variables from .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    
    # Get GitHub token from environment variable
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token or github_token == 'your_github_token_here':
        logger.error("GitHub token not found in .env file")
        return None
    
    # Load other configuration from config.ini
    config = ConfigParser()
    config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    if not os.path.exists(config_file):
        logger.error(f"Config file {config_file} does not exist")
        return None
    
    config.read(config_file)
    
    # Combine token from .env with other settings from config.ini
    try:
        github_config = {
            'token': github_token,
            'owner': config['github']['owner'],
            'repo': config['github']['repo']
        }
        logger.info("GitHub configuration loaded successfully")
        return github_config
    except Exception as e:
        logger.error(f"Error loading GitHub configuration: {e}")
        return None


async def run_collector_agent(task_id: str = None, task_title: str = None, output_file: str = None) -> Dict[str, Any]:
    """Run the collector agent and return/save the results"""
    config = await load_config_async()
    if not config:
        logger.error("Failed to load configuration")
        return {"error": "Configuration loading failed"}
    
    agent = CollectorAgent(config, task_id, task_title)
    results = await agent.run()
    
    if output_file:
        context_md = agent.generate_context_document(output_file)
        logger.info(f"Saved context document to {output_file}")
    
    return results


async def run_executor_agent(task_type: str, task_id: str, task_title: str, 
                           context: Dict[str, Any] = None, code_input: str = None,
                           output_dir: str = None) -> Dict[str, Any]:
    """Run the executor agent and return/save the results"""
    config = await load_config_async()
    if not config:
        logger.error("Failed to load configuration")
        return {"error": "Configuration loading failed"}
    
    agent = ExecutorAgent(config, task_id, task_title, "claude-3-opus", context)
    results = await agent.run(task_type, code_input)
    
    if output_dir and "error" not in results:
        saved_files = agent.save_results(output_dir)
        results["saved_files"] = saved_files
    
    return results


async def main():
    """Main function for CLI operation"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  ai_agents.py collect [task_id] [task_title] [output_file]")
        print("  ai_agents.py execute <task_type> <task_id> <task_title> [output_dir]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "collect":
        task_id = sys.argv[2] if len(sys.argv) > 2 else None
        task_title = sys.argv[3] if len(sys.argv) > 3 else None
        output_file = sys.argv[4] if len(sys.argv) > 4 else os.path.join("docs", "context_priming.md")
        
        print(f"Running collector agent for task: {task_title or 'General collection'}")
        results = await run_collector_agent(task_id, task_title, output_file)
        
        if "error" in results:
            print(f"Error: {results['error']}")
            sys.exit(1)
        else:
            print(f"Successfully collected context data and saved to {output_file}")
    
    elif command == "execute":
        if len(sys.argv) < 5:
            print("Usage: ai_agents.py execute <task_type> <task_id> <task_title> [output_dir]")
            print("Task types: code_generation, improvement_recommendations")
            sys.exit(1)
        
        task_type = sys.argv[2]
        task_id = sys.argv[3]
        task_title = sys.argv[4]
        output_dir = sys.argv[5] if len(sys.argv) > 5 else os.path.join("docs", "ai_output")
        
        print(f"Running executor agent for task #{task_id}: {task_title}")
        
        # First collect context
        context = await run_collector_agent(task_id, task_title)
        if "error" in context:
            print(f"Warning: Could not collect context: {context['error']}")
            context = {}
        
        # Then execute the task
        results = await run_executor_agent(task_type, task_id, task_title, context, None, output_dir)
        
        if "error" in results:
            print(f"Error: {results['error']}")
            sys.exit(1)
        else:
            print(f"Successfully executed {task_type} task")
            if "saved_files" in results:
                print("Generated files:")
                for file in results["saved_files"]:
                    print(f"  - {file}")
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: collect, execute")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())