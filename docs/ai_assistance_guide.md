# AI Assistance Guide

This guide outlines how AI assistance is integrated into the project workflow system, providing details on context priming, token usage tracking, and automated documentation features.

## Overview

The project workflow system has been enhanced with AI-driven features to improve efficiency, reduce context-switching costs, and optimize AI interactions. Key features include:

1. **AI Context Priming**: Automatically gathers relevant project data to provide AI assistants with comprehensive context.
2. **Token Usage Tracking**: Monitors AI API usage to optimize costs and reduce token waste.
3. **Task-Specific Context**: Links related issues and provides AI-optimized context for specific tasks.

## Project Basics

- **Project Structure:** Review the recommended project structure in [project_structure.md](project_structure.md).
- **Work Tracking:** Monitor task statuses using [work_tracking.md](work_tracking.md) and GitHub Issues.
- **Task Templates:** Refer to the task templates in the `docs/tasks` folder and `.github/ISSUE_TEMPLATE`.
- **GitHub Integration:** Automated task management with GitHub Issues integration.

## AI Context Priming

### How It Works

The context priming module (`scripts/context_priming.py`) extracts relevant project information and compiles it into an AI-friendly format:

```
python scripts/context_priming.py [optional: "Task Title"]
```

- **Without Task Title**: Generates general project context
- **With Task Title**: Includes task-specific context and related issues

### Generated Context Includes

- Project overview (from README)
- Directory structure
- Recent commits
- Open and recently closed issues
- Task-related issues (if task title provided)

The context is stored in `docs/context_priming.md` and automatically linked to new task files.

### Integration with Task Creation

When creating a new task with `start_task.py`, context priming is automatically run:

```
python scripts/start_task.py "Your Task Title"
```

This creates:
- A GitHub issue with links to related issues
- A local task file with a link to the generated context
- Optimized context for AI assistants

## Token Usage Tracking

### Features

The token tracking system (`scripts/token_tracker.py`) helps manage and optimize AI API costs by:

- Logging token usage per task, API, and time period
- Generating usage reports
- Providing token-saving recommendations

### Usage

```
# Log token usage
python scripts/token_tracker.py log <task_id> <task_title> <api_name> <prompt_tokens> <completion_tokens> [notes]

# View monthly report
python scripts/token_tracker.py report month [YYYY-MM]

# View task-specific report
python scripts/token_tracker.py report task <task_id>

# Get token-saving recommendations
python scripts/token_tracker.py report tips
```

### Integration

- Automatic token tracking during context generation
- Task files include links to view token usage
- Monthly summaries for cost management

## Task Management Process

1. **Setting Up:**
   - Ensure your GitHub token is set in the `.env` file in the `scripts` directory.
   - Verify your GitHub repository information in `scripts/config.ini`.

2. **Starting Tasks:**
   - Run `python scripts/start_task.py "Your Task Title"` to create a GitHub issue, generate AI context, and create a local task file.
   - The script will check for duplicates before creating new issues.
   - Local task files are stored in `docs/tasks/TASK-{issue_number}.md` with links to AI context.

3. **Working with AI:**
   - Reference the context primer when working with AI assistants.
   - Track token usage for cost optimization.
   - Use the auto-generated context to give AI better understanding of the project.

4. **Completing Tasks:**
   - Run `python scripts/finish_task.py "Your Task Title" "Optional verification notes"` to close the GitHub issue.
   - This will add a comment to the issue, close it, and update your local task file.
   - If issues arise, check the log files in the `logs` directory for details.

## Best Practices for AI Interaction

1. **Provide Context Links**: When asking AI for help with a task, include a link to the context priming document.

2. **Use Task-Specific Context**: Reference the task-specific context generated for each task when working with AI assistants.

3. **Consider Token Optimization**: Review token usage reports regularly and implement recommendations to reduce unnecessary token consumption.

4. **Update Context When Needed**: If project structure changes significantly, regenerate the context primer.

5. **Include Related Issues**: Reference related issues in your prompts to give AI better understanding of task history and connections.

## Example Workflow

1. Start a new task with context priming:
   ```
   python scripts/start_task.py "Implement user authentication"
   ```

2. Include the context primer link when working with AI assistants:
   ```
   "I'm working on implementing user authentication. 
   Here's the project context: [link to context_priming.md]"
   ```

3. Track token usage for the task:
   ```
   python scripts/token_tracker.py report task <issue_number>
   ```

4. Complete the task and close the issue:
   ```
   python scripts/finish_task.py "Implement user authentication" "Completed with JWT-based auth system"
   ```

## Troubleshooting

- **Context Generation Errors**: If context priming fails, the system will fall back to creating issues without context. Check GitHub token permissions and network connectivity.

- **Token Tracking Issues**: If token tracking reports show inconsistencies, verify that the token logs haven't been corrupted.

- **Missing Related Issues**: If related issues aren't appearing, try regenerating the context with more specific keywords in the task title.

## References

- [Project Workflow Guide (README)](../README.md)
- [AI Task Guide](ai_task_guide.md)
- [Work Tracking](work_tracking.md)
- [GitHub Issue Template](../.github/ISSUE_TEMPLATE/task.md)
- [GitHub PR Template](../.github/PULL_REQUEST_TEMPLATE.md)