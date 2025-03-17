# AI Assistance Guide

This guide serves as a quick reference for users to understand the project's structure, processes, and conventions with GitHub integration.

## Overview

- **Project Structure:** Review the recommended project structure in [project_structure.md](project_structure.md).
- **Work Tracking:** Monitor task statuses using [work_tracking.md](work_tracking.md) and GitHub Issues.
- **Task Templates:** Refer to the task templates in the `docs/tasks` folder and `.github/ISSUE_TEMPLATE`.
- **GitHub Integration:** Automated task management with GitHub Issues integration.

## Task Management Process

1. **Setting Up:**
   - Ensure your GitHub token is set in the `.env` file in the `scripts` directory.
   - Verify your GitHub repository information in `scripts/config.ini`.

2. **Starting Tasks:**
   - Run `python scripts/start_task.py "Your Task Title"` to create a GitHub issue and local task file.
   - The script will check for duplicates before creating new issues.
   - Local task files are stored in `docs/tasks/TASK-{issue_number}.md`.

3. **Completing Tasks:**
   - Run `python scripts/finish_task.py "Your Task Title" "Optional verification notes"` to close the GitHub issue.
   - This will add a comment to the issue, close it, and update your local task file.
   - If issues arise, check the log files in the `logs` directory for details.

4. **Creating Pull Requests:**
   - Use the provided PR template in `.github/PULL_REQUEST_TEMPLATE.md` when submitting changes.
   - Link PRs to issues using GitHub syntax (e.g., "Closes #123").

## Error Handling

If you encounter errors:
1. Check the logs in the `logs` directory for detailed information.
2. Verify your GitHub token and repository settings.
3. Retry the command - scripts include automatic retry logic for API failures.

## References

- [Project Workflow Guide (README)](../README.md)
- [AI Task Guide](ai_task_guide.md)
- [Work Tracking](work_tracking.md)
- [GitHub Issue Template](../.github/ISSUE_TEMPLATE/task.md)
- [GitHub PR Template](../.github/PULL_REQUEST_TEMPLATE.md)
