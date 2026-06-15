"""
test_parser.py — Pengujian utilitas AST parser dan traversal.

Memverifikasi kebenaran fungsi-fungsi di core/parser.py yang menjadi
fondasi bagi semua rule di knowledge_base.py.

Author  : Kelompok AI Code Review Tutor (Testing & Evaluasi)
NIM     : 241011124 — Muhammad Akmal Ahsan
Course  : Kecerdasan Buatan, Semester Genap 2025/2026
"""

import ast
import pytest
from core.parser import (
    parse_source,
    attach_parents,
    bfs_traverse,
    get_snippet,
    nesting_depth,
    is_inside_function,
    has_break,
    is_constant_true,
    find_strings_in_compare_or_assign,
    AnalysisContext,
)


# ═══════════════════════════════════════════════════════════════════════════
# parse_source
# ═══════════════════════════════════════════════════════════════════════════
class TestParseSource:
    def test_kode_valid_menghasilkan_module(self):
        tree = parse_source("x = 1 + 2")
        assert isinstance(tree, ast.Module)

    def test_kode_kosong_tetap_valid(self):
        tree = parse_source("")
        assert isinstance(tree, ast.Module)

    def test_syntax_error_dilempar(self):
        with pytest.raises(SyntaxError):
            parse_source("def foo(:\n    pass")

    def test_multi_baris_valid(self):
        code = "def foo():\n    return 1\n\nx = foo()"
        tree = parse_source(code)
        assert isinstance(tree, ast.Module)


# ═══════════════════════════════════════════════════════════════════════════
# attach_parents
# ═══════════════════════════════════════════════════════════════════════════
class TestAttachParents:
    def test_setiap_child_memiliki_parent(self):
        """Setiap node child harus punya atribut _parent yang menunjuk ke parent-nya."""
        tree = parse_source("x = 1 + 2")
        attach_parents(tree)
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                assert hasattr(child, "_parent")
                assert child._parent is parent

    def test_root_tidak_memiliki_parent(self):
        """Root node (Module) tidak memiliki _parent."""
        tree = parse_source("x = 1")
        attach_parents(tree)
        assert not hasattr(tree, "_parent")

    def test_parent_adalah_langsung_bukan_leluhur(self):
        """_parent harus parent langsung, bukan nenek moyang yang lebih jauh."""
        tree = parse_source("x = 1 + 2")
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                assert node.left._parent is node
                assert node.right._parent is node


# ═══════════════════════════════════════════════════════════════════════════
# bfs_traverse
# ═══════════════════════════════════════════════════════════════════════════
class TestBfsTraverse:
    def test_mengembalikan_list(self):
        tree = parse_source("x = 1")
        assert isinstance(bfs_traverse(tree), list)

    def test_root_adalah_elemen_pertama(self):
        """Root node harus menjadi elemen pertama dalam BFS."""
        tree = parse_source("x = 1")
        nodes = bfs_traverse(tree)
        assert nodes[0] is tree

    def test_semua_node_hadir(self):
        """BFS harus menghasilkan jumlah node yang sama dengan ast.walk."""
        tree = parse_source("x = 1 + 2")
        bfs_set = set(id(n) for n in bfs_traverse(tree))
        walk_set = set(id(n) for n in ast.walk(tree))
        assert bfs_set == walk_set

    def test_kode_kosong_hanya_module(self):
        """Kode kosong → BFS hanya berisi satu node (Module)."""
        tree = parse_source("")
        nodes = bfs_traverse(tree)
        assert len(nodes) >= 1
        assert isinstance(nodes[0], ast.Module)


# ═══════════════════════════════════════════════════════════════════════════
# get_snippet
# ═══════════════════════════════════════════════════════════════════════════
class TestGetSnippet:
    def test_snippet_mengandung_teks_kode(self):
        code = "x = 1 + 2\ny = x * 3"
        tree = parse_source(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and hasattr(node, "lineno"):
                snippet = get_snippet(node, code)
                assert len(snippet) > 0
                break

    def test_snippet_tidak_lebih_dari_max_lines(self):
        """get_snippet dengan max_lines=1 harus menghasilkan maksimal 1 baris."""
        code = "def foo():\n    x = 1\n    return x\n"
        tree = parse_source(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                snippet = get_snippet(node, code, max_lines=1)
                assert "\n" not in snippet
                break

    def test_node_tanpa_lineno_menghasilkan_string_kosong(self):
        """Node tanpa lineno harus mengembalikan string kosong."""
        dummy = ast.AST()
        result = get_snippet(dummy, "x = 1")
        assert result == ""


# ═══════════════════════════════════════════════════════════════════════════
# nesting_depth
# ═══════════════════════════════════════════════════════════════════════════
class TestNestingDepth:
    def test_depth_nol_di_level_modul(self):
        """Node di level modul (tanpa parent nesting) harus memiliki depth 0."""
        tree = parse_source("x = 1")
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                assert nesting_depth(node) == 0

    def test_depth_bertambah_dalam_fungsi(self):
        """Node di dalam fungsi harus memiliki depth >= 1."""
        tree = parse_source("def foo():\n    x = 1")
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                assert nesting_depth(node) >= 1

    def test_depth_bertambah_dengan_nesting(self):
        """Node yang lebih dalam harus memiliki depth lebih besar."""
        code = """
def foo():
    if True:
        for i in range(1):
            x = i
"""
        tree = parse_source(code)
        attach_parents(tree)
        assign_depths = [
            nesting_depth(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
        ]
        assert max(assign_depths) >= 3

    def test_depth_tepat_empat_level(self):
        """Struktur dengan 4 tingkat nesting → depth harus tepat 4."""
        code = """
def proses():
    if True:
        for i in range(1):
            if True:
                x = i
"""
        tree = parse_source(code)
        attach_parents(tree)
        assign_depths = [
            nesting_depth(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
        ]
        assert max(assign_depths) == 4


# ═══════════════════════════════════════════════════════════════════════════
# is_inside_function
# ═══════════════════════════════════════════════════════════════════════════
class TestIsInsideFunction:
    def test_node_di_luar_fungsi(self):
        """Node di level modul → is_inside_function harus False."""
        tree = parse_source("x = 1")
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                assert not is_inside_function(node)

    def test_node_di_dalam_fungsi(self):
        """Node di dalam FunctionDef → is_inside_function harus True."""
        tree = parse_source("def foo():\n    x = 1")
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                assert is_inside_function(node)

    def test_node_dalam_fungsi_bersarang(self):
        """Node di dalam fungsi yang bersarang → tetap True."""
        code = """
def outer():
    def inner():
        x = 1
"""
        tree = parse_source(code)
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                assert is_inside_function(node)


# ═══════════════════════════════════════════════════════════════════════════
# has_break
# ═══════════════════════════════════════════════════════════════════════════
class TestHasBreak:
    def test_loop_dengan_break(self):
        """while True dengan break → has_break harus True."""
        tree = parse_source("while True:\n    break")
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                assert has_break(node)

    def test_loop_tanpa_break(self):
        """while True tanpa break → has_break harus False."""
        tree = parse_source("while True:\n    x = 1")
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                assert not has_break(node)

    def test_break_di_nested_loop_tidak_dihitung(self):
        """Break di nested loop (for di dalam while) tidak dihitung untuk outer loop."""
        code = """
while True:
    for i in range(10):
        break
    x = 1
"""
        tree = parse_source(code)
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                assert not has_break(node)

    def test_break_di_if_dalam_loop(self):
        """Break di dalam if yang ada di dalam loop → dihitung untuk loop."""
        code = """
while True:
    if kondisi:
        break
"""
        tree = parse_source(code)
        attach_parents(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                assert has_break(node)


# ═══════════════════════════════════════════════════════════════════════════
# is_constant_true
# ═══════════════════════════════════════════════════════════════════════════
class TestIsConstantTrue:
    def test_true_literal(self):
        """while True → kondisi harus dikenali sebagai constant True."""
        tree = parse_source("while True:\n    pass")
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                assert is_constant_true(node.test)

    def test_false_literal(self):
        """while False → bukan constant True."""
        tree = parse_source("while False:\n    pass")
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                assert not is_constant_true(node.test)

    def test_variabel_bukan_constant_true(self):
        """while aktif → bukan constant True."""
        tree = parse_source("while aktif:\n    pass")
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                assert not is_constant_true(node.test)

    def test_integer_satu_adalah_true(self):
        """while 1 → sama dengan while True, dianggap constant True."""
        tree = parse_source("while 1:\n    pass")
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                assert is_constant_true(node.test)


# ═══════════════════════════════════════════════════════════════════════════
# find_strings_in_compare_or_assign
# ═══════════════════════════════════════════════════════════════════════════
class TestFindStrings:
    def test_string_dalam_compare_dihitung(self):
        """String dalam konteks Compare harus dihitung."""
        code = 'if role == "admin": pass'
        tree = parse_source(code)
        attach_parents(tree)
        counts = find_strings_in_compare_or_assign(tree)
        assert counts.get("admin", 0) >= 1

    def test_string_dalam_assign_dihitung(self):
        """String dalam konteks Assign harus dihitung."""
        code = 'status = "aktif"'
        tree = parse_source(code)
        attach_parents(tree)
        counts = find_strings_in_compare_or_assign(tree)
        assert counts.get("aktif", 0) >= 1

    def test_string_dalam_print_tidak_dihitung(self):
        """String dalam print() (bukan Compare/Assign) tidak dihitung."""
        code = 'print("halo dunia")'
        tree = parse_source(code)
        attach_parents(tree)
        counts = find_strings_in_compare_or_assign(tree)
        assert counts.get("halo dunia", 0) == 0

    def test_string_berulang_dihitung_benar(self):
        """String yang muncul dua kali dalam Assign → count harus 2."""
        code = 'a = "aktif"\nb = "aktif"'
        tree = parse_source(code)
        attach_parents(tree)
        counts = find_strings_in_compare_or_assign(tree)
        assert counts.get("aktif", 0) == 2


# ═══════════════════════════════════════════════════════════════════════════
# AnalysisContext
# ═══════════════════════════════════════════════════════════════════════════
class TestAnalysisContext:
    def test_context_memiliki_semua_atribut(self):
        """AnalysisContext harus memiliki source, tree, bfs_nodes, string_counts, scratch."""
        code = "x = 1"
        tree = parse_source(code)
        attach_parents(tree)
        ctx = AnalysisContext(code, tree)
        assert hasattr(ctx, "source")
        assert hasattr(ctx, "tree")
        assert hasattr(ctx, "bfs_nodes")
        assert hasattr(ctx, "string_counts")
        assert hasattr(ctx, "scratch")

    def test_bfs_nodes_adalah_list(self):
        code = "x = 1 + 2"
        tree = parse_source(code)
        attach_parents(tree)
        ctx = AnalysisContext(code, tree)
        assert isinstance(ctx.bfs_nodes, list)
        assert len(ctx.bfs_nodes) > 0

    def test_scratch_awalnya_kosong(self):
        code = "x = 1"
        tree = parse_source(code)
        attach_parents(tree)
        ctx = AnalysisContext(code, tree)
        assert ctx.scratch == {}
