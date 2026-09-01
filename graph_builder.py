import os
import json
import ast
from typing import Dict, List, Any

def extract_function_calls(file_path: str) -> List[str]:
    """Helper to extract top-level function and method call names from a file using AST."""
    calls = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
    except Exception:
        pass
    return list(set(calls))

def build_dependency_graph(repo_graph_path: str = "repo_graph.json") -> Dict[str, Any]:
    """Resolves cross-file import relationships, class inheritances, and symbol references."""
    if not os.path.exists(repo_graph_path):
        raise FileNotFoundError(f"Missing {repo_graph_path}. Run repo_scanner.py first.")

    with open(repo_graph_path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    file_nodes = graph_data.get("files", {})
    
    # Map raw module/file names to relative paths
    module_to_file = {}
    for rel_path in file_nodes.keys():
        module_name = rel_path.replace("\\", "/").replace(".py", "").replace("/", ".")
        module_to_file[module_name] = rel_path
        base_name = os.path.basename(rel_path).replace(".py", "")
        module_to_file[base_name] = rel_path

    resolved_edges = []
    symbol_table = {}  # Symbol -> file mapping for inherited classes and function calls

    # Build symbol mapping table across all files
    for rel_path, data in file_nodes.items():
        for func in data.get("functions", []):
            symbol_table[func["name"]] = rel_path
        for cls in data.get("classes", []):
            symbol_table[cls["name"]] = rel_path

    for src_file, data in file_nodes.items():
        # 1. Resolve direct imports
        for imp in data.get("imports", []):
            target_module = imp.get("module") or imp.get("name")
            if not target_module:
                continue

            resolved_target = module_to_file.get(target_module)
            if not resolved_target:
                root_pkg = target_module.split(".")[0]
                resolved_target = module_to_file.get(root_pkg)

            if resolved_target and resolved_target != src_file:
                resolved_edges.append({
                    "source": src_file,
                    "target": resolved_target,
                    "type": "import",
                    "symbol": imp.get("name"),
                    "line": imp.get("line")
                })

        # 2. Map class inheritance relationships
        for cls in data.get("classes", []):
            for base_cls in cls.get("bases", []):
                if base_cls in symbol_table and symbol_table[base_cls] != src_file:
                    resolved_edges.append({
                        "source": src_file,
                        "target": symbol_table[base_cls],
                        "type": "inherits",
                        "symbol": f"{cls['name']} -> {base_cls}",
                        "line": cls["start_line"]
                    })

        # 3. Map cross-file function calls
        full_src_path = os.path.join(graph_data.get("repo_path", ""), src_file)
        if os.path.exists(full_src_path):
            calls = extract_function_calls(full_src_path)
            for call_symbol in calls:
                if call_symbol in symbol_table and symbol_table[call_symbol] != src_file:
                    resolved_edges.append({
                        "source": src_file,
                        "target": symbol_table[call_symbol],
                        "type": "function_call",
                        "symbol": call_symbol,
                        "line": None
                    })

    # Deduplicate edges
    unique_edges = [dict(t) for t in {tuple(d.items()) for d in resolved_edges}]
    graph_data["dependency_edges"] = unique_edges
    return graph_data

if __name__ == "__main__":
    updated_graph = build_dependency_graph()
    
    with open("repo_graph.json", "w", encoding="utf-8") as f:
        json.dump(updated_graph, f, indent=2)

    print(f"Graph mapping complete. Resolved {len(updated_graph['dependency_edges'])} total dependency edges.")
