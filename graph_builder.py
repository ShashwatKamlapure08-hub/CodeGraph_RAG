import json
import os

def build_dependency_graph(json_path: str = "repo_graph.json"):
    """Reads the scanned repo graph, resolves module imports and inheritance, and populates dependency edges."""
    if not os.path.exists(json_path):
        return {"total_files": 0, "files": {}, "dependency_edges": []}

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    files_dict = data.get("files", {})
    edges = []

    # Map module/file names for lookup (e.g., "vector_store.py" -> "vector_store", etc.)
    file_name_map = {}
    for file_path in files_dict.keys():
        base_name = os.path.basename(file_path).replace(".py", "")
        file_name_map[base_name] = file_path

    # Build edges based on imports and class inheritance
    for file_path, file_info in files_dict.items():
        # 1. Process Imports
        for imp in file_info.get("imports", []):
            imp_name = imp.get("name") or imp.get("module")
            if imp_name:
                top_module = imp_name.split(".")[0]
                if top_module in file_name_map:
                    target_file = file_name_map[top_module]
                    if target_file != file_path:
                        edge = {"source": file_path, "target": target_file, "type": "import"}
                        if edge not in edges:
                            edges.append(edge)

        # 2. Process Class Inheritances
        for cls in file_info.get("classes", []):
            for base in cls.get("bases", []):
                base_clean = base.split(".")[0]
                if base_clean in file_name_map:
                    target_file = file_name_map[base_clean]
                    if target_file != file_path:
                        edge = {"source": file_path, "target": target_file, "type": "inheritance"}
                        if edge not in edges:
                            edges.append(edge)

    data["dependency_edges"] = edges

    # Save back updated graph
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return data

if __name__ == "__main__":
    build_dependency_graph()
    print("Dependency graph built successfully with resolved edges!")
