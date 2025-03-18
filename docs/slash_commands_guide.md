# AI-Powered Slash Commands Guide

This guide covers the available slash commands that leverage AI to enhance your development workflow.

## Commands Overview

| Command | Description | Output |
|---------|-------------|--------|
| `/check-bugs` | Fetches unresolved GitHub issues | Markdown report with bugs highlighted |
| `/summarize-docs` | Summarizes README documentation | Concise summary with key sections |
| `/generate-tests` | Creates unit tests for recent code changes | Python test code files |

## Usage

Each slash command can be run from the terminal:

```bash
python scripts/slash_commands.py /command-name [options]
```

### Global Options

- `--brief_mode`: Reduces token consumption by generating more concise outputs
- `--output` or `-o`: Specifies a file to save the output (defaults to stdout)

## Command Details

### `/check-bugs`

Fetches all open issues from GitHub and identifies bug-related issues by their labels.

```bash
python scripts/slash_commands.py /check-bugs
python scripts/slash_commands.py /check-bugs --output reports/bugs.md
```

Output includes:
- Issues labeled as bugs listed separately
- Associated labels for each issue
- Links to GitHub issue pages
- Count of bug and non-bug issues

### `/summarize-docs`

Analyzes the project README and generates a concise summary of its key information.

```bash
python scripts/slash_commands.py /summarize-docs
```

Output includes:
- Project title and description
- Key features
- Setup steps
- Brief overview of main sections

### `/generate-tests`

Analyzes recently modified Python files and generates unit tests for them.

```bash
python scripts/slash_commands.py /generate-tests
```

Output includes:
- Generated test classes and functions
- Test fixtures and assertions
- Coverage for each method in the source files

## Token Usage Optimization

The slash commands are designed to be efficient with token usage. To further optimize:

1. Use the `--brief_mode` flag to reduce output verbosity
2. Generate tests only for specific files when needed
3. Weekly or bi-weekly runs of bug checks rather than daily

## Implementation Details

The slash commands use the `SlashCommandsAgent` class which inherits from `BaseAgent` to handle:

1. GitHub API interactions
2. AI prompting and response generation
3. Token usage tracking
4. Output formatting

## Extending With New Commands

To add a new slash command:

1. Add a new method to the `SlashCommandsAgent` class
2. Update the `run()` method to handle the new command
3. Add a formatter method for the output
4. Document the new command here

## Troubleshooting

Common issues:

- **GitHub API rate limiting**: Wait a few minutes and try again
- **Missing GitHub token**: Ensure your `.env` file contains a valid `GITHUB_TOKEN`
- **Permissions issues**: Verify your GitHub token has appropriate read permissions