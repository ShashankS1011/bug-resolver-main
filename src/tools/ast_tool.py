import ast
from typing import Dict, Any, List

class ASTAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.summary = {
            "classes": [],
            "functions": [],
            "imports": []
        }

    def visit_Import(self, node):
        for alias in node.names:
            self.summary["imports"].append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.summary["imports"].append(f"{module}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({
                    "name": item.name,
                    "lineno": item.lineno,
                    "args": [arg.arg for arg in item.args.args]
                })
        
        self.summary["classes"].append({
            "name": node.name,
            "lineno": node.lineno,
            "docstring": ast.get_docstring(node),
            "methods": methods
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Only top-level functions (class methods are handled in visit_ClassDef)
        if not isinstance(getattr(node, 'parent', None), ast.ClassDef):
            self.summary["functions"].append({
                "name": node.name,
                "lineno": node.lineno,
                "docstring": ast.get_docstring(node),
                "args": [arg.arg for arg in node.args.args]
            })
        self.generic_visit(node)

def parse_code_structure(code: str) -> Dict[str, Any]:
    """Parses raw Python code and builds an architectural summary."""
    try:
        tree = ast.parse(code)
        
        # Attach parent references to distinguish top-level functions from methods
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent
                
        analyzer = ASTAnalyzer()
        analyzer.visit(tree)
        return analyzer.summary
    except SyntaxError as e:
        return {"error": f"Failed to parse AST due to SyntaxError: {str(e)}"}