#!/usr/bin/env python
import sys
import os

def main():
    if len(sys.argv) < 3:
        print("Usage: finish_task.py WORKITEM_NUMBER 'Verification Results'")
        sys.exit(1)
    workitem = sys.argv[1]
    verification = sys.argv[2]
    task_filename = os.path.join("docs", "tasks", f"WORKITEM-{workitem}.md")
    if not os.path.exists(task_filename):
        print(f"Task file {task_filename} does not exist. Please create it first using start_task.py")
        sys.exit(1)
    # Append verification results to the file
    with open(task_filename, "a") as f:
        f.write(f"\n## Verification Results\n- {verification}\n")
    print(f"Task file {task_filename} updated with verification results.")

if __name__ == "__main__":
    main()
