# AI Task Guide

This guide serves as a central hub for AI assistants to understand the project's structure, processes, and conventions with GitHub integration.

## Overview

- **Project Structure:** Review the recommended project structure in [project_structure.md](project_structure.md).
- **Work Tracking:** Refer to [work_tracking.md](work_tracking.md) to monitor task statuses.
- **Task Templates:** Use the task template provided in the `tasks` folder for documenting new tasks.
- **GitHub Integration:** Scripts automatically create and close GitHub issues as tasks are started and completed.

## Task Workflow

1. Before starting a task, review the current work tracking and guidelines.

2. **Starting a Task:**
   - Use the `scripts/start_task.py` script to create a new GitHub issue and local task file:
     ```
     python scripts/start_task.py "Your Task Title"
     ```
   - This will:
     - Check for duplicate issues with the same title
     - Create a new GitHub issue with the "Task" label
     - Generate a local markdown file in `docs/tasks/TASK-{issue_number}.md`
     - Log the process in the `logs` directory

3. **Working on a Task:**
   - Update the local task file with your implementation notes, testing steps, etc.
   - Commit your changes using standard Git practices
   - When creating a Pull Request, use the template provided in `.github/PULL_REQUEST_TEMPLATE.md`

4. **Completing a Task:**
   - Use the `scripts/finish_task.py` script to close the GitHub issue and update the local task file:
     ```
     python scripts/finish_task.py "Your Task Title" "Optional verification notes"
     ```
   - This will:
     - Find the matching GitHub issue by title
     - Add a comment with your verification notes
     - Close the issue
     - Update the local task file with verification results
     - Log the process in the `logs` directory

## Error Handling

- Scripts include retry logic with exponential backoff for API failures
- All actions are logged to files in the `logs` directory
- User-friendly error messages guide through troubleshooting
- Special handling for cases like:
  - Duplicate issue detection
  - Already closed issues
  - Multiple issues with similar titles

## References

- [Project Workflow Guide (README)](../README.md)
- [AI Assistance Guide](ai_assistance_guide.md)
- [Work Tracking](work_tracking.md)
- [GitHub Issue Template](.github/ISSUE_TEMPLATE/task.md)
- [GitHub PR Template](.github/PULL_REQUEST_TEMPLATE.md)
