import ast
from typing import Dict, List, Any

class CodeASTParser(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports = []
        self.functions = []
        self.classes = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append({
                "type": "import",
                "name": alias.name,
                "alias": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "type": "from_import",
                "module": module,
                "name": alias.name,
                "alias": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)

    def _get_annotation_str(self, node_arg: ast.arg) -> str:
        """Extracts string representations of type annotations."""
        if node_arg.annotation:
            return ast.unparse(node_arg.annotation)
        return "Any"

    def visit_FunctionDef(self, node: ast.FunctionDef):
        args = [
            {
                "name": arg.arg,
                "type": self._get_annotation_str(arg)
            }
            for arg in node.args.args
        ]
        
        returns = ast.unparse(node.returns) if node.returns else "None"
        docstring = ast.get_docstring(node) or ""

        self.functions.append({
            "name": node.name,
            "args": args,
            "returns": returns,
            "docstring": docstring,
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno)
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_args = [
                    {
                        "name": arg.arg,
                        "type": self._get_annotation_str(arg)
                    }
                    for arg in item.args.args
                ]
                method_returns = ast.unparse(item.returns) if item.returns else "None"
                method_doc = ast.get_docstring(item) or ""

                class_methods.append({
                    "name": item.name,
                    "args": method_args,
                    "returns": method_returns,
                    "docstring": method_doc,
                    "start_line": item.lineno,
                    "end_line": getattr(item, "end_lineno", item.lineno)
                })

        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(base.attr)

        class_doc = ast.get_docstring(node) or ""

        self.classes.append({
            "name": node.name,
            "bases": base_classes,
            "docstring": class_doc,
            "methods": class_methods,
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno)
        })


def parse_file(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    tree = ast.parse(code, filename=file_path)
    parser = CodeASTParser(file_path)
    parser.visit(tree)

    return {
        "file_path": file_path,
        "imports": parser.imports,
        "functions": parser.functions,
        "classes": parser.classes
    }
