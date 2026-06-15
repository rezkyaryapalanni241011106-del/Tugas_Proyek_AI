"""
parser.py — AST Parser dan utilitas traversal.

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
"""

import ast
from collections import deque
from typing import Dict, List


def parse_source(source: str) -> ast.AST:
    """Parse kode Python (string) menjadi AST root node."""
    return ast.parse(source)


def attach_parents(tree: ast.AST) -> None:
    """Pasang atribut `_parent` ke setiap node sebagai referensi ke parent-nya."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child._parent = parent


def bfs_traverse(tree: ast.AST) -> List[ast.AST]:
    """Traversal Breadth-First Search atas seluruh AST."""
    result: List[ast.AST] = []
    queue: deque = deque([tree])
    while queue:
        node = queue.popleft()
        result.append(node)
        for child in ast.iter_child_nodes(node):
            queue.append(child)
    return result


def get_snippet(node: ast.AST, source: str, max_lines: int = 3) -> str:
    """Ekstrak potongan kode aktual yang menjadi tempat node."""
    if not hasattr(node, "lineno"):
        return ""
    lines = source.splitlines()
    start = node.lineno - 1
    end = getattr(node, "end_lineno", node.lineno) - 1
    end = min(end, start + max_lines - 1, len(lines) - 1)
    snippet_lines = lines[start:end + 1]
    return "\n".join(snippet_lines).strip()


_NESTING_TYPES = (
    ast.For, ast.AsyncFor, ast.While, ast.If,
    ast.Try, ast.With, ast.AsyncWith,
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
)


def nesting_depth(node: ast.AST) -> int:
    """Hitung kedalaman nesting node dari root ke node ini."""
    depth = 0
    current = getattr(node, "_parent", None)
    while current is not None:
        if isinstance(current, _NESTING_TYPES):
            depth += 1
        current = getattr(current, "_parent", None)
    return depth


def is_inside_function(node: ast.AST) -> bool:
    """True jika node berada di dalam FunctionDef atau AsyncFunctionDef."""
    current = getattr(node, "_parent", None)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return True
        current = getattr(current, "_parent", None)
    return False


def has_break(loop_node: ast.AST) -> bool:
    """Cek apakah ada `break` di body loop ini (bukan di nested loop)."""
    def _walk(n: ast.AST) -> bool:
        if isinstance(n, ast.Break):
            return True
        if n is not loop_node and isinstance(n, (ast.For, ast.While, ast.AsyncFor)):
            return False
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return False
        for child in ast.iter_child_nodes(n):
            if _walk(child):
                return True
        return False
    return _walk(loop_node)


def is_constant_true(node: ast.AST) -> bool:
    """Cek apakah node merepresentasikan konstanta True (untuk R14)."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return node.value is True
        if isinstance(node.value, int):
            return node.value == 1
        return False
    return False


def find_strings_in_compare_or_assign(tree: ast.AST) -> Dict[str, int]:
    """Hitung kemunculan setiap string literal dalam konteks Compare/Assign."""
    counts: Dict[str, int] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        parent = getattr(node, "_parent", None)
        while parent is not None:
            if isinstance(parent, (ast.Compare, ast.Assign)):
                counts[node.value] = counts.get(node.value, 0) + 1
                break
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.ClassDef, ast.Module)):
                break
            parent = getattr(parent, "_parent", None)
    return counts


class AnalysisContext:
    """Container info global yang dipakai oleh rules selama analisis."""

    def __init__(self, source: str, tree: ast.AST):
        self.source = source
        self.tree = tree
        self.bfs_nodes: List[ast.AST] = bfs_traverse(tree)
        self.string_counts: Dict[str, int] = find_strings_in_compare_or_assign(tree)
        self.scratch: Dict[str, object] = {}
