from src.tools.ast_tool import parse_code_structure

sample_code = """
import os
import sys

class Calculator:
    \"\"\"Simple calculator class.\"\"\"
    def add(self, a, b):
        return a + b

def standalone_helper(val):
    return val * 2
"""

parsed = parse_code_structure(sample_code)
print("AST Output:")
print(parsed)