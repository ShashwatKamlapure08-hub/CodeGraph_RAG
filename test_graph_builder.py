import os
import json
import tempfile
import pytest
from repo_scanner import scan_repository
from graph_builder import build_dependency_graph

# Sample multi-file repo structure simulation
FILE_A = '''"""Module A"""
class ParentBase:
    def base_method(self):
        return "base"
'''

FILE_B = '''"""Module B"""
from file_a import ParentBase

class ChildClass(ParentBase):
    def child_method(self):
        return self.base_method()
'''

@pytest.fixture
def mock_repo_dir():
    """Sets up a temporary directory with two interdependent python files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path_a = os.path.join(temp_dir, "file_a.py")
        path_b = os.path.join(temp_dir, "file_b.py")

        with open(path_a, "w", encoding="utf-8") as f:
            f.write(FILE_A)
        with open(path_b, "w", encoding="utf-8") as f:
            f.write(FILE_B)

        yield temp_dir

def test_graph_resolution_pipeline(mock_repo_dir):
    # Step 1: Run repo scanner on temporary repository
    scanned_graph = scan_repository(mock_repo_dir)
    assert scanned_graph["total_files"] == 2

    # Save to temp path for graph builder
    graph_path = os.path.join(mock_repo_dir, "repo_graph.json")
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(scanned_graph, f)

    # Step 2: Run dependency graph resolution
    resolved_graph = build_dependency_graph(graph_path)
    edges = resolved_graph.get("dependency_edges", [])

    assert len(edges) > 0

    # Verify import edge from file_b to file_a
    import_edges = [e for e in edges if e["type"] == "import"]
    assert any(e["source"] == "file_b.py" and "file_a.py" in e["target"] for e in import_edges)

    # Verify inheritance edge (ChildClass -> ParentBase)
    inherits_edges = [e for e in edges if e["type"] == "inherits"]
    assert any("ParentBase" in e["symbol"] for e in inherits_edges)
