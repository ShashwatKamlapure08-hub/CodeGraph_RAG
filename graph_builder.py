import os
import json
from typing import Dict, List, Any

def build_dependency_graph(repo_graph_path: str = "repo_graph.json") -> Dict[str, Any]:
    """Resolves cross-file import relationships and builds a directed code dependency graph."""
    if not os.path.exists(repo_graph_path):
        raise FileNotFoundError(f"Missing {repo_graph_path}. Run repo_scanner.py first.")

    with open(repo_graph_path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    file_nodes = graph_data.get("files", {})
    
    # Map raw module names to relative file paths within the project
    module_to_file = {}
    for rel_path in file_nodes.keys():
        # Converts path 'utils/helpers.py' -> 'utils.helpers' or 'helpers'
        module_name = rel_path.replace("\\", "/").replace(".py", "").replace("/", ".")
        module_to_file[module_name] = rel_path
        # Also map base file name for direct imports (e.g. 'code_parser')
        base_name = os.path.basename(rel_path).replace(".py", "")
        module_to_file[base_name] = rel_path

    resolved_edges = []
    
    for src_file, data in file_nodes.items():
        imports = data.get("imports", [])
        
        for imp in imports:
            target_module = imp.get("module") or imp.get("name")
            if not target_module:
                continue

            # Check if imported module matches local codebase files
            resolved_target = None
            if target_module in module_to_file:
                resolved_target = module_to_file[target_module]
            else:
                # Try matching root module package name
                root_pkg = target_module.split(".")[0]
                if root_pkg in module_to_file:
                    resolved_target = module_to_file[root_pkg]

            if resolved_target:
                resolved_edges.append({
                    "source": src_file,
                    "target": resolved_target,
                    "imported_symbol": imp.get("name"),
                    "line": imp.get("line")
                })

    graph_data["dependency_edges"] = resolved_edges
    return graph_data

if __name__ == "__main__":
    updated_graph = build_dependency_graph()
    
    with open("repo_graph.json", "w", encoding="utf-8") as f:
        json.dump(updated_graph, f, indent=2)

    print(f"Dependency mapping complete. Resolved {len(updated_graph['dependency_edges'])} internal edges.")
