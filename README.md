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
    ├── slash_commands.py    # AI-powered slash commands for workflow
    └── config.ini           # Configuration for GitHub repository
```

## Key Features

- **GitHub Integration**: Automatically create and close GitHub issues as you start and finish tasks
- **Local Task Management**: Generate and update local markdown files for detailed task documentation
- **Error Handling**: Robust error recovery with retry mechanisms and detailed logging
- **Standardized Templates**: PR and Issue templates for consistent GitHub workflow
- **AI-Powered Slash Commands**: Quick commands to improve development workflow

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

### Slash Commands

For quick workflow actions, use these AI-powered slash commands:

- `/check-bugs`: Fetch unresolved GitHub issues, highlighting ones labeled as bugs
  ```bash
  python scripts/slash_commands.py /check-bugs
  ```

- `/summarize-docs`: Generate an AI summary of the README
  ```bash
  python scripts/slash_commands.py /summarize-docs
  ```

- `/generate-tests`: AI generates unit tests for recent code changes
  ```bash
  python scripts/slash_commands.py /generate-tests
  ```

To reduce token consumption, add the `--brief_mode` flag:
```bash
python scripts/slash_commands.py /check-bugs --brief_mode
```

Feel free to modify these templates as needed for your project.