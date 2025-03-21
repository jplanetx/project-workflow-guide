# AI Context Primer

*Generated on: 2025-03-18 00:30:31*

## Current Task: Test Parallel Execution

Task ID: context_priming

## Project Overview

# Project Workflow Guide

This repository provides templates and guidelines to set up your project following our established workflow with GitHub integration.

## Directory Structure

```
project-workflow-guide/
├── README.md
├── HOW_TO_USE.md
├── .github/                 # GitHub templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       └── task.md
├── docs/
│   ├── ai_task_guide.md
│   ├── ai_assistance_guide.md
│   ├── work_tracking.md
│   ├── project_structure.md
│   ├── strategic_plan/
│   │   ├── current_state_analysis.md
│   │   ├── project_charter.md
│   │   └── user_research_template.md
│   └── tasks/
│       └── TASK_TEMPLATE.md
├── logs/                    # Generated log files from scripts
└── scripts/
    ├── start_task.py        # Creates GitHub issues and local task files
    ├── finish_task.py       # Closes GitHub issues and updates local files
    ├── task_logger.py       # Logging utility for scripts
    └── config.ini           # Configuration for GitHub repository
```

## Key Features

- **GitHub Integration**: Automatically create and close GitHub issues as you start and finish tasks
- **Local Task Management**: Generate and update local markdown files for detailed task documentation
- **Error Handling**: Robust error recovery with retry mechanisms and detailed logging
- **Standardized Templates**: PR and Issue templates for consistent GitHub workflow

## Setup

1. Clone this repository into your new project
2. Configure GitHub integration:
   - Create a `.env` file in the `scripts` directory with your GitHub token: `GITHUB_TOKEN=your_token_here`
   - Update the `config.ini` file with your GitHub username and repository name
3. Install required dependencies: `pip install -r requirements.txt`

## Usage

1. Review the documents in the `docs` folder for guidelines on setting up tasks, tracking work, and managing project structure
2. Start a new task: `python scripts/start_task.py "Your Task Title"`
3. Finish a task: `python scripts/finish_task.py "Your Task Title" "Optional verification notes"`

Feel free to modify these templates as needed for your project.


## Recent Commits

- [b932da1] Add logging utility, update requirements, and create GitHub templates - *jplanetx* on 2025-03-17
- [df1c792] Initial commit - *jplanetx* on 2025-03-17

## Open Issues


## Recently Closed Issues


## Project Structure

```
{
  "docs/": {
    "ai_assistance_guide.md": null,
    "ai_task_guide.md": null,
    "project_structure.md": null,
    "strategic_plan/": {
      "current_state_analysis.md": null,
      "project_charter.md": null,
      "user_research_template.md": null
    },
    "tasks/": {
      "TASK_TEMPLATE.md": null
    },
    "work_tracking.md": null
  },
  "HOW_TO_USE.md": null,
  "logs/": {
    "ai_agents_20250318.log": null,
    "start_task_20250318.log": null,
    "token_tracker_20250318.log": null,
    "token_usage/": {
      "token_usage_202503.csv": null
    }
  },
  "README.md": null,
  "requirements-fixed.txt": null,
  "requirements-simple.txt": null,
  "requirements.txt": null,
  "scripts/": {
    "ai_agents.py": null,
    "config.ini": null,
    "context_priming.py": null,
    "finish_task.py": null,
    "start_task.py": null,
    "task_logger.py": null,
    "token_tracker.py": null,
    "__pycache__/": {
      "ai_agents.cpython-312.pyc": null,
      "task_logger.cpython-312.pyc": null,
      "token_tracker.cpython-312.pyc": null
    }
  }
}
```
