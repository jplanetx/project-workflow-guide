# Project Structure & Guidelines

This document outlines a recommended project directory structure and provides guidelines for organizing your code and assets. Use this as a reference when setting up a new project based on the workflow guidelines.

## Recommended Directory Layout

A typical project might follow a structure similar to the one below:

```
project-root/
├── config/                  # Configuration files (e.g., config.json, config_schema.json)
├── docs/                    # Documentation
│   ├── ai_task_guide.md     # AI task guide
│   ├── ai_assistance_guide.md  # AI assistance guide
│   ├── work_tracking.md     # Work tracking document
│   └── tasks/               # Task-specific documents (e.g., WORKITEM-XXX.md)
├── scripts/                 # Utility scripts for tasks like starting or finishing work items
├── src/                     # Source code for the application
│   ├── core/                # Core functionalities and business logic
│   ├── utils/               # Utility functions and helper modules
│   └── ...                  # Other modules and components
├── tests/                   # Test suite (unit tests, integration tests, etc.)
└── README.md                # Project overview and setup instructions
```

## Guidelines

- **Configuration:**  
  Place all configuration files in the `config/` directory. Ensure that configuration schemas are documented for validation purposes.

- **Documentation:**  
  Maintain up-to-date documentation in the `docs/` folder. Use the provided templates (e.g., work_tracking.md) to track progress and detail tasks.

- **Source Code Organization:**  
  Organize your source code into meaningful modules in the `src/` directory. Separate core functionality, utilities, and specific features into dedicated subdirectories.

- **Scripts:**  
  Place automation scripts (e.g., for starting or finishing tasks) in the `scripts/` directory. These scripts help streamline the development process.

- **Testing:**  
  Keep your tests organized within the `tests/` directory. Aim for high test coverage to ensure the reliability of your application.

This structure can be adjusted based on project-specific needs but provides a strong foundation to maintain consistency and quality across projects.
