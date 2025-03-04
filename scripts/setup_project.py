#!/usr/bin/env python3
import os

def create_project_structure():
    """
    Creates a standard Python project directory structure:
      - src: for your source code
      - tests: for your test suites
      - scripts: for utility scripts or executables
      - terraform: for your infrastructure-as-code files (e.g., Terraform)
    """
    directories = [
        "src",
        "tests",
        "scripts",
        "terraform",
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
        except Exception as e:
            print(f"Error creating {directory}: {e}")

if __name__ == "__main__":
    create_project_structure()
