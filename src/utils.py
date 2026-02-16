"""
Utility functions for the Python-AST-RAG project.
"""

import os
from typing import List


def read_file(file_path: str) -> str:
    """
    Reads the content of a file.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: Content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def get_all_python_files(directory: str) -> List[str]:
    """
    Recursively finds all Python files in a directory.

    Args:
        directory (str): The directory to search.

    Returns:
        List[str]: A list of paths to Python files.
    """
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files
