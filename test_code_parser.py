import os
import tempfile
import pytest
from code_parser import parse_file

# Sample Python script string to parse during testing
SAMPLE_CODE = '''"""Module level docstring."""

import os
from typing import List

def sample_function(param_a: int, param_b: str = "default") -> bool:
    """A test standalone function."""
    result = True
    return result

class SampleClass:
    """A test class definition."""
    def __init__(self, name: str):
        self.name = name

    def compute(self, values: List[int]) -> int:
        """Computes sum of values."""
        return sum(values)
'''

@pytest.fixture
def sample_file():
    """Fixture that creates a temporary python file for testing."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_f:
        temp_f.write(SAMPLE_CODE)
        temp_f.flush()
        temp_path = temp_f.name
    
    yield temp_path

    # Cleanup after test runs
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_imports_extraction(sample_file):
    parsed = parse_file(sample_file)
    imports = parsed["imports"]
    
    assert len(imports) == 2
    assert imports[0]["name"] == "os"
    assert imports[1]["module"] == "typing"
    assert imports[1]["name"] == "List"

def test_function_parsing(sample_file):
    parsed = parse_file(sample_file)
    functions = parsed["functions"]
    
    assert len(functions) == 1
    fn = functions[0]
    assert fn["name"] == "sample_function"
    assert fn["returns"] == "bool"
    assert fn["docstring"] == "A test standalone function."
    assert len(fn["args"]) == 2
    assert fn["args"][0]["name"] == "param_a"
    assert fn["args"][0]["type"] == "int"
    # Ensure start and end line bounds are preserved
    assert fn["start_line"] > 0
    assert fn["end_line"] >= fn["start_line"]

def test_class_and_method_parsing(sample_file):
    parsed = parse_file(sample_file)
    classes = parsed["classes"]
    
    assert len(classes) == 1
    cls = classes[0]
    assert cls["name"] == "SampleClass"
    assert cls["docstring"] == "A test class definition."
    assert len(cls["methods"]) == 2
    
    method_names = [m["name"] for m in cls["methods"]]
    assert "__init__" in method_names
    assert "compute" in method_names

    compute_method = next(m for m in cls["methods"] if m["name"] == "compute")
    assert compute_method["returns"] == "int"
    assert compute_method["start_line"] > 0
    assert compute_method["end_line"] >= compute_method["start_line"]
