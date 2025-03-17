# Work Tracking

This document tracks the progress of all work items in the project. Task tracking is now integrated with GitHub Issues for streamlined management.

## Tracking Methods

### 1. GitHub Issues
- The primary source of truth for task tracking is GitHub Issues
- Each task is represented as a GitHub Issue with the "Task" label
- Use the integrated scripts to create and close issues automatically

### 2. Local Task Documentation
- Detailed documentation for each task is stored in `docs/tasks/TASK-{issue_number}.md`
- These files contain implementation notes, testing steps, and verification results
- They are automatically generated and updated by the task scripts

## Active Work Items

Active work items can be viewed:
- On the GitHub Issues page with state "open"
- In the local task files that don't have verification results

For reference, you can list active work items here using the template:
```
### Task: [Task Title]
Issue: #[issue_number]
Status: [In Progress]
Description: [Brief description]
```

## Completed Work Items

Completed work items can be viewed:
- On the GitHub Issues page with state "closed"
- In the local task files that include verification results

For reference, you can list completed work items here using the template:
```
### Task: [Task Title]
Issue: #[issue_number]
Completed: [Date]
Verification: [Brief description of verification]
```
