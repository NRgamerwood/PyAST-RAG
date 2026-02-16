"""
Parser module for extracting structured code chunks from Python source files using AST.
"""

import ast
from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """
    Metadata for a code chunk.

    Attributes:
        file_path (str): The path to the source file.
        node_type (str): The type of the node (e.g., "function", "class").
        name (str): The name of the function or class.
        line_range (Tuple[int, int]): The start and end line numbers.
        parent_name (Optional[str]): The name of the parent class, if any.
        dependencies (List[str]): A list of detected function calls or attribute accesses.
    """
    file_path: str
    node_type: str
    name: str
    line_range: Tuple[int, int]
    parent_name: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class CodeChunk(BaseModel):
    """
    A structured code chunk extracted from source code.

    Attributes:
        content (str): The raw source code of the chunk.
        metadata (ChunkMetadata): Associated metadata.
    """
    content: str
    metadata: ChunkMetadata


class ChunkVisitor(ast.NodeVisitor):
    """
    AST Visitor to traverse the tree and extract Class and Function definitions.
    """

    def __init__(self, source_code: str, file_path: str):
        """
        Initialize the visitor.

        Args:
            source_code (str): The full source code of the file.
            file_path (str): The path to the file.
        """
        self.source_code = source_code
        self.file_path = file_path
        self.chunks: List[CodeChunk] = []
        self.parent_stack: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        """Processes a class definition."""
        chunk = self._create_chunk(node, "class")
        self.chunks.append(chunk)

        self.parent_stack.append(node.name)
        self.generic_visit(node)
        self.parent_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Processes a function definition."""
        chunk = self._create_chunk(node, "function")
        self.chunks.append(chunk)

        # We don't push functions to parent_stack to avoid nested function parent tracking
        # as usually we care about the class context.
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Processes an async function definition."""
        chunk = self._create_chunk(node, "function")
        self.chunks.append(chunk)
        self.generic_visit(node)

    def _create_chunk(self, node: Any, node_type: str) -> CodeChunk:
        """
        Creates a CodeChunk from an AST node.

        Args:
            node: The AST node.
            node_type: The type of the node.

        Returns:
            CodeChunk: The created chunk.
        """
        parent_name = self.parent_stack[-1] if self.parent_stack else None

        # Extract source content
        content = ast.get_source_segment(self.source_code, node) or ""

        # Extract dependencies (simple call detection)
        dependencies = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    dependencies.add(child.func.attr)

        metadata = ChunkMetadata(
            file_path=self.file_path,
            node_type=node_type,
            name=node.name,
            line_range=(node.lineno, node.end_lineno),
            parent_name=parent_name,
            dependencies=list(dependencies)
        )

        return CodeChunk(content=content, metadata=metadata)


class ASTParser:
    """
    Parser for Python source code using AST.
    """

    def parse_source(self, source_code: str, file_path: str) -> List[CodeChunk]:
        """
        Parses the given source code.

        Args:
            source_code (str): The Python source code.
            file_path (str): The path to the file (for metadata).

        Returns:
            List[CodeChunk]: A list of extracted code chunks.
        """
        try:
            tree = ast.parse(source_code)
            visitor = ChunkVisitor(source_code, file_path)
            visitor.visit(tree)
            return visitor.chunks
        except SyntaxError as e:
            # In a real RAG system, we might want to log this
            print(f"Syntax error parsing {file_path}: {e}")
            return []
