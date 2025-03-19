#!/usr/bin/env python
import os
import sys
import json
import time
import csv
from datetime import datetime
from configparser import ConfigParser
from dotenv import load_dotenv

# Import our custom logger
from scripts.task_logger import setup_logger

# Set up logger
logger = setup_logger('token_tracker')

class TokenTracker:
    def __init__(self):
        # Create token tracking directory if it doesn't exist
        self.tracking_dir = os.path.join(os.path.dirname(__file__), '..', 'logs', 'token_usage')
        os.makedirs(self.tracking_dir, exist_ok=True)
        
        # Path to the token usage CSV file
        self.token_log_file = os.path.join(self.tracking_dir, f"token_usage_{datetime.now().strftime('%Y%m')}.csv")
        
        # Path to the token usage summary JSON file
        self.token_summary_file = os.path.join(self.tracking_dir, "token_usage_summary.json")
        
        # Initialize token usage statistics
        self.init_token_log()
        self.load_or_create_summary()
    
    def init_token_log(self):
        """Initialize the token usage log file if it doesn't exist."""
        if not os.path.exists(self.token_log_file):
            logger.info(f"Creating new token usage log file: {self.token_log_file}")
            with open(self.token_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'task_id', 'task_title', 'api_name', 'endpoint', 
                                 'prompt_tokens', 'completion_tokens', 'total_tokens', 'estimated_cost', 'notes'])
    
    def load_or_create_summary(self):
        """Load the token usage summary or create it if it doesn't exist."""
        if os.path.exists(self.token_summary_file):
            try:
                with open(self.token_summary_file, 'r') as f:
                    self.summary = json.load(f)
                logger.debug(f"Loaded token usage summary from {self.token_summary_file}")
            except Exception as e:
                logger.error(f"Error loading token usage summary: {e}")
                self.create_new_summary()
        else:
            self.create_new_summary()
    
    def create_new_summary(self):
        """Create a new token usage summary structure."""
        self.summary = {
            'total_tokens': 0,
            'total_cost': 0.0,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'by_task': {},
            'by_month': {},
            'by_api': {},
            'last_updated': datetime.now().isoformat(),
            'token_saving_tips': []
        }
        logger.info("Created new token usage summary")
    
    def log_token_usage(self, task_id, task_title, api_name, endpoint, prompt_tokens, completion_tokens, notes=""):
        """Log token usage for an API call."""
        # Calculate totals
        total_tokens = prompt_tokens + completion_tokens
        
        # Estimate cost (can be updated with actual pricing)
        cost_rates = {
            'gpt-3.5-turbo': {'prompt': 0.0000015, 'completion': 0.000002},
            'gpt-4': {'prompt': 0.00003, 'completion': 0.00006},
            'claude-3-opus': {'prompt': 0.00001, 'completion': 0.00003},
            'claude-3-sonnet': {'prompt': 0.000003, 'completion': 0.000015},
            'default': {'prompt': 0.000005, 'completion': 0.000015}
        }
        
        # Get appropriate cost rate
        rate = cost_rates.get(api_name, cost_rates['default'])
        estimated_cost = (prompt_tokens * rate['prompt']) + (completion_tokens * rate['completion'])
        
        # Log to CSV
        timestamp = datetime.now().isoformat()
        with open(self.token_log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, task_id, task_title, api_name, endpoint, 
                            prompt_tokens, completion_tokens, total_tokens, estimated_cost, notes])
        
        # Update summary
        current_month = datetime.now().strftime('%Y-%m')
        
        # Update total counts
        self.summary['total_tokens'] += total_tokens
        self.summary['total_cost'] += estimated_cost
        self.summary['prompt_tokens'] += prompt_tokens
        self.summary['completion_tokens'] += completion_tokens
        self.summary['last_updated'] = timestamp
        
        # Update by task
        if task_id not in self.summary['by_task']:
            self.summary['by_task'][task_id] = {
                'title': task_title,
                'total_tokens': 0,
                'total_cost': 0.0,
                'query_count': 0
            }
        
        self.summary['by_task'][task_id]['total_tokens'] += total_tokens
        self.summary['by_task'][task_id]['total_cost'] += estimated_cost
        self.summary['by_task'][task_id]['query_count'] += 1
        
        # Update by month
        if current_month not in self.summary['by_month']:
            self.summary['by_month'][current_month] = {
                'total_tokens': 0,
                'total_cost': 0.0,
                'query_count': 0
            }
        
        self.summary['by_month'][current_month]['total_tokens'] += total_tokens
        self.summary['by_month'][current_month]['total_cost'] += estimated_cost
        self.summary['by_month'][current_month]['query_count'] += 1
        
        # Update by API
        if api_name not in self.summary['by_api']:
            self.summary['by_api'][api_name] = {
                'total_tokens': 0,
                'total_cost': 0.0,
                'query_count': 0
            }
        
        self.summary['by_api'][api_name]['total_tokens'] += total_tokens
        self.summary['by_api'][api_name]['total_cost'] += estimated_cost
        self.summary['by_api'][api_name]['query_count'] += 1
        
        # Save updated summary
        self.save_summary()
        
        # Generate token saving recommendations if total tokens is large
        self.generate_token_saving_tips(prompt_tokens, task_title)
        
        logger.info(f"Logged {total_tokens} tokens (${estimated_cost:.6f}) for task {task_id}: {task_title}")
        return {
            'total_tokens': total_tokens,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'estimated_cost': estimated_cost
        }
    
    def save_summary(self):
        """Save the token usage summary to a file."""
        try:
            with open(self.token_summary_file, 'w') as f:
                json.dump(self.summary, f, indent=2)
            logger.debug(f"Saved token usage summary to {self.token_summary_file}")
        except Exception as e:
            logger.error(f"Error saving token usage summary: {e}")
    
    def generate_token_saving_tips(self, prompt_tokens, task_title):
        """Generate token saving tips based on usage patterns."""
        # Check if prompt is unusually large
        if prompt_tokens > 4000:
            tip = {
                'type': 'large_prompt',
                'task': task_title,
                'tokens': prompt_tokens,
                'suggestion': 'Consider breaking down large prompts into smaller, focused queries. Extract only the most relevant context.',
                'timestamp': datetime.now().isoformat()
            }
            self.summary['token_saving_tips'].append(tip)
            logger.info(f"Generated token saving tip for large prompt ({prompt_tokens} tokens)")
        
        # Limit the number of tips stored
        if len(self.summary['token_saving_tips']) > 10:
            self.summary['token_saving_tips'] = self.summary['token_saving_tips'][-10:]
        
        self.save_summary()
    
    def get_monthly_report(self, month=None):
        """Generate a monthly usage report."""
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        if month in self.summary['by_month']:
            monthly_data = self.summary['by_month'][month]
            report = {
                'month': month,
                'total_tokens': monthly_data['total_tokens'],
                'total_cost': monthly_data['total_cost'],
                'query_count': monthly_data['query_count'],
                'avg_tokens_per_query': monthly_data['total_tokens'] / monthly_data['query_count'] if monthly_data['query_count'] > 0 else 0
            }
            return report
        else:
            logger.warning(f"No data available for month: {month}")
            return None
    
    def get_task_report(self, task_id):
        """Generate a usage report for a specific task."""
        if task_id in self.summary['by_task']:
            task_data = self.summary['by_task'][task_id]
            report = {
                'task_id': task_id,
                'title': task_data['title'],
                'total_tokens': task_data['total_tokens'],
                'total_cost': task_data['total_cost'],
                'query_count': task_data['query_count'],
                'avg_tokens_per_query': task_data['total_tokens'] / task_data['query_count'] if task_data['query_count'] > 0 else 0
            }
            return report
        else:
            logger.warning(f"No data available for task: {task_id}")
            return None
    
    def get_token_saving_recommendations(self):
        """Get token saving recommendations."""
        # Basic static recommendations
        static_recommendations = [
            "Use specific, focused queries instead of broad, open-ended ones",
            "Extract only the necessary code snippets or documentation for context",
            "For large codebases, reference file paths rather than including full file contents",
            "Break complex tasks into smaller, focused subtasks",
            "Use the most cost-effective AI model appropriate for the task"
        ]
        
        # Combine static recommendations with dynamic tips
        all_recommendations = static_recommendations.copy()
        for tip in self.summary['token_saving_tips']:
            all_recommendations.append(f"{tip['suggestion']} (Example: {tip['task']})")
        
        return all_recommendations

def print_usage():
    """Print usage instructions for the CLI"""
    print("Usage:")
    print("  token_tracker.py log <task_id> <task_title> <api_name> <prompt_tokens> <completion_tokens> [notes]")
    print("  token_tracker.py report [month|task <task_id>|tips]")

def handle_log_command(tracker, args):
    """Handle the 'log' command"""
    if len(args) < 5:
        print("Missing arguments for log command.")
        print("Usage: token_tracker.py log <task_id> <task_title> <api_name> <prompt_tokens> <completion_tokens> [notes]")
        sys.exit(1)
    
    task_id = args[0]
    task_title = args[1]
    api_name = args[2]
    
    try:
        prompt_tokens = int(args[3])
        completion_tokens = int(args[4])
    except ValueError:
        print("Token counts must be integers.")
        sys.exit(1)
    
    notes = args[5] if len(args) > 5 else ""
    
    result = tracker.log_token_usage(
        task_id=task_id,
        task_title=task_title,
        api_name=api_name,
        endpoint="completion",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        notes=notes
    )
    
    print(f"Logged {result['total_tokens']} tokens (${result['estimated_cost']:.6f}):")
    print(f"  - Prompt tokens: {result['prompt_tokens']}")
    print(f"  - Completion tokens: {result['completion_tokens']}")

def handle_month_report(tracker, args):
    """Handle the 'report month' command"""
    month = args[0] if args else None
    report = tracker.get_monthly_report(month)
    
    if report:
        print(f"Token Usage Report for {report['month']}:")
        print(f"  - Total tokens: {report['total_tokens']}")
        print(f"  - Total cost: ${report['total_cost']:.4f}")
        print(f"  - Total queries: {report['query_count']}")
        print(f"  - Average tokens per query: {report['avg_tokens_per_query']:.1f}")
    else:
        print("No data available for the specified month.")

def handle_task_report(tracker, args):
    """Handle the 'report task' command"""
    if not args:
        print("Missing task ID.")
        print("Usage: token_tracker.py report task <task_id>")
        sys.exit(1)
        
    task_id = args[0]
    report = tracker.get_task_report(task_id)
    
    if report:
        print(f"Token Usage Report for Task #{report['task_id']} ({report['title']}):")
        print(f"  - Total tokens: {report['total_tokens']}")
        print(f"  - Total cost: ${report['total_cost']:.4f}")
        print(f"  - Total queries: {report['query_count']}")
        print(f"  - Average tokens per query: {report['avg_tokens_per_query']:.1f}")
    else:
        print(f"No data available for task {task_id}.")

def handle_tips_report(tracker):
    """Handle the 'report tips' command"""
    recommendations = tracker.get_token_saving_recommendations()
    print("Token Saving Recommendations:")
    for i, tip in enumerate(recommendations, 1):
        print(f"{i}. {tip}")

def handle_report_command(tracker, args):
    """Handle the 'report' command"""
    report_type = args[0] if args else "month"
    remaining_args = args[1:]
    
    if report_type == "month":
        handle_month_report(tracker, remaining_args)
    elif report_type == "task":
        handle_task_report(tracker, remaining_args)
    elif report_type == "tips":
        handle_tips_report(tracker)
    else:
        print(f"Unknown report type: {report_type}")
        print("Available report types: month, task, tips")

def main():
    """Main function for CLI token tracking."""
    tracker = TokenTracker()
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    command_args = sys.argv[2:]
    
    if command == "log":
        handle_log_command(tracker, command_args)
    elif command == "report":
        handle_report_command(tracker, command_args)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: log, report")
        sys.exit(1)

if __name__ == "__main__":
    main()