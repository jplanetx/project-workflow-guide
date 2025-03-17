# How to Use This Template

This repository is a self-contained project workflow guide and template that applies our standardized process to any project with GitHub integration. You can clone this repository and integrate its contents into your project to ensure consistent task management, documentation, and development practices.

## Steps to Apply the Template

1. **Clone the Repository:**
   - Run:
     ```
     git clone https://github.com/your-username/project-workflow-guide.git
     ```
   - Alternatively, download the repository as a ZIP file and extract it.

2. **Set Up GitHub Integration:**
   - Create a GitHub Personal Access Token with "Issues" and "Metadata" permissions.
   - Create a `.env` file in the `scripts` directory with your GitHub token:
     ```
     GITHUB_TOKEN=your_token_here
     ```
   - Update `scripts/config.ini` with your GitHub username and repository name:
     ```
     [github]
     owner = your-github-username
     repo = your-repository-name
     ```
   - Install required Python packages:
     ```
     pip install -r requirements.txt
     ```

3. **Integrate Into Your Project:**
   - Copy the following folders and files into your new project's root directory:
     - `.github/` (contains PR and issue templates)
     - `docs/` (contains guidelines, task templates, and project structure recommendations)
     - `scripts/` (contains utility scripts for task management and GitHub integration)
     - `README.md` (overview and instructions)
     - `HOW_TO_USE.md` (this file, with application instructions)
   - You can keep the repository structure intact or merge relevant parts into your existing project.

4. **Customize as Needed:**
   - Review and update the documents in the `docs` folder to reflect any project-specific details.
   - Customize the scripts in the `scripts` folder if your project has additional requirements.
   - Modify the templates in `.github/` to match your project's needs.
   - Use the task template in `docs/tasks/TASK_TEMPLATE.md` to document new work items.

5. **Start Your Work:**
   - Use the provided scripts to manage work items and GitHub issues:
     - `python scripts/start_task.py "Task Title"` - Creates a GitHub issue and local task file
     - `python scripts/finish_task.py "Task Title" "Verification notes"` - Closes the GitHub issue and updates the task file
   - Refer to the AI Task Guide and AI Assistance Guide for best practices.

## Benefits

- **GitHub Integration:** Automatically create and close issues as you work on tasks.
- **PR Templates:** Standardized pull request format for better code reviews.
- **Issue Templates:** Structured issue creation for clearer task definition.
- **Consistency:** Apply a standard process across all projects.
- **Documentation:** Keep clear records of tasks, implementation decisions, and testing outcomes.
- **Error Handling:** Robust error recovery and detailed logging for troubleshooting.
- **Task Management:** Easily create, update, and finish work items using simple scripts.

This template is designed to be adaptable and serves as a guide to streamline the development process with GitHub. Use it as a foundation to ensure high-quality outcomes and maintain alignment with project goals.
