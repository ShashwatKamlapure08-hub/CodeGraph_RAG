import os
import json
from typing import Dict, List, Any
from code_parser import parse_file

# File/folder patterns to skip during repository traversal
IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", "env", "build", "dist", ".pytest_cache"}
IGNORE_FILES = {"__init__.py"}

def scan_repository(repo_path: str) -> Dict[str, Any]:
    """Recursively parses all Python files in a directory into a single structured graph."""
    repo_graph = {
        "repo_path": os.path.abspath(repo_path),
        "total_files": 0,
        "files": {}
    }

    for root, dirs, files in os.walk(repo_path):
        # In-place filter to ignore unwanted directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file.endswith(".py") and file not in IGNORE_FILES:
                full_path = os.path.join(root, file)
                # Compute clean relative path to use as node identifier
                rel_path = os.path.relpath(full_path, repo_path)

                try:
                    parsed_data = parse_file(full_path)
                    repo_graph["files"][rel_path] = parsed_data
                    repo_graph["total_files"] += 1
                except SyntaxError:
                    print(f"[Warning] Skipped invalid syntax in file: {rel_path}")
                except Exception as e:
                    print(f"[Warning] Failed to parse {rel_path}: {e}")

    return repo_graph

if __name__ == "__main__":
    # Test execution on the current working directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    graph = scan_repository(current_dir)
    
    # Save graph schema for verification
    with open("repo_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    print(f"Successfully scanned {graph['total_files']} files. Graph saved to repo_graph.json")
