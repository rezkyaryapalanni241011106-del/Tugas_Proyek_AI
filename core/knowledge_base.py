"""
knowledge_base.py — Knowledge Base berisi 15 RULES Antipattern.

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
"""

import ast
import difflib
from abc import ABC, abstractmethod
from itertools import combinations
from typing import List, Set

from .models import Severity, Violation
from .parser import (
    AnalysisContext, get_snippet, nesting_depth,
    is_inside_function, has_break, is_constant_true,
)


# ============================================================
# Base classes
# ============================================================

class Rule(ABC):
    rule_id: str = ""
    rule_name: str = ""
    severity: Severity = Severity.LOW


class PerNodeRule(Rule):
    @abstractmethod
    def condition(self, node: ast.AST, ctx: AnalysisContext) -> bool:
        pass

    def make_violation(self, node: ast.AST, ctx: AnalysisContext) -> Violation:
        return Violation(
            rule_id=self.rule_id,
            line_no=getattr(node, "lineno", 0),
            severity=self.severity,
            snippet=get_snippet(node, ctx.source),
            rule_name=self.rule_name,
        )


class GlobalRule(Rule):
    @abstractmethod
    def evaluate(self, ctx: AnalysisContext) -> List[Violation]:
        pass


# ============================================================
# RULES R01 – R14 (per-node)
# ============================================================

class R01_BareExcept(PerNodeRule):
    rule_id = "R01_bare_except"
    rule_name = "Bare except (except tanpa tipe Exception)"
    severity = Severity.HIGH

    def condition(self, node, ctx):
        return isinstance(node, ast.ExceptHandler) and node.type is None


class R02_NonDescriptiveName(PerNodeRule):
    rule_id = "R02_non_descriptive_name"
    rule_name = "Nama variabel tidak deskriptif (1 huruf)"
    severity = Severity.MEDIUM
    ALLOWED = {"i", "j", "k", "x", "y", "n", "_"}

    def condition(self, node, ctx):
        if isinstance(node, ast.arg):
            return len(node.arg) == 1 and node.arg not in self.ALLOWED
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            return len(node.id) == 1 and node.id not in self.ALLOWED
        return False

    def make_violation(self, node, ctx):
        v = super().make_violation(node, ctx)
        name = node.arg if isinstance(node, ast.arg) else node.id
        v.snippet = f"nama: '{name}'   →   {v.snippet}"
        return v


class R03_MissingDocstring(PerNodeRule):
    rule_id = "R03_missing_docstring"
    rule_name = "Fungsi tanpa docstring"
    severity = Severity.LOW
    MIN_BODY = 5  # Fungsi pendek (<5 statement) tidak diwajibkan punya docstring

    def condition(self, node, ctx):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        if not node.body:
            return True
        # Fungsi pendek tidak perlu docstring — menambah noise tanpa nilai edukasi
        if len(node.body) < self.MIN_BODY:
            return False
        first = node.body[0]
        return not (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        )


class R04_MagicNumber(PerNodeRule):
    rule_id = "R04_magic_number"
    rule_name = "Magic Number (angka tanpa nama/konteks)"
    severity = Severity.MEDIUM
    ALLOWED = {0, 1, -1}

    def condition(self, node, ctx):
        if not isinstance(node, ast.Constant):
            return False
        if isinstance(node.value, bool):
            return False
        if not isinstance(node.value, (int, float)):
            return False
        if node.value in self.ALLOWED:
            return False
        parent = getattr(node, "_parent", None)
        # Angka yang menjadi argumen langsung sebuah fungsi bukan "magic number"
        # dalam arti sesungguhnya — itu hanya data yang diteruskan, bukan konstanta
        # logika yang tertanam tanpa nama. Cukup kecualikan semua ast.Call.
        if isinstance(parent, ast.Call):
            return False
        if isinstance(parent, ast.Expr):
            return False
        return True


class R05_DeepNesting(PerNodeRule):
    rule_id = "R05_deep_nesting"
    rule_name = "Nesting terlalu dalam (>4 tingkat)"
    severity = Severity.HIGH
    _NEST = (ast.If, ast.For, ast.While, ast.Try, ast.With,
             ast.AsyncFor, ast.AsyncWith)

    def condition(self, node, ctx):
        if not isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
            return False
        if nesting_depth(node) <= 4:
            return False
        # Laporkan HANYA node terdangkal yang pertama menembus batas. Tanpa ini,
        # satu struktur bersarang dalam (mis. if di dalam if di dalam if...) akan
        # menghasilkan banyak violation berulang untuk masalah yang sama.
        parent = getattr(node, "_parent", None)
        while parent is not None:
            if isinstance(parent, self._NEST):
                # Ada leluhur kontrol yang juga sudah menembus batas → biarkan
                # leluhur itu yang dilaporkan, node ini cukup diabaikan.
                return nesting_depth(parent) <= 4
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.ClassDef)):
                break
            parent = getattr(parent, "_parent", None)
        return True


class R06_LongFunction(PerNodeRule):
    rule_id = "R06_long_function"
    rule_name = "Fungsi terlalu panjang (>20 statement)"
    severity = Severity.MEDIUM
    MAX_BODY = 20

    def condition(self, node, ctx):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        return len(node.body) > self.MAX_BODY


class R07_TooManyParams(PerNodeRule):
    rule_id = "R07_too_many_params"
    rule_name = "Fungsi punya terlalu banyak parameter (>5)"
    severity = Severity.MEDIUM
    MAX_PARAMS = 5

    def condition(self, node, ctx):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        return len(node.args.args) > self.MAX_PARAMS


class R08_MutableDefault(PerNodeRule):
    rule_id = "R08_mutable_default"
    rule_name = "Default argument mutable (list/dict/set)"
    severity = Severity.HIGH

    def condition(self, node, ctx):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                return True
        return False


class R09_PrintDebug(PerNodeRule):
    rule_id = "R09_print_debug"
    rule_name = "print() di dalam fungsi (kemungkinan sisa debug)"
    severity = Severity.LOW

    def condition(self, node, ctx):
        if not isinstance(node, ast.Call):
            return False
        if not isinstance(node.func, ast.Name):
            return False
        if node.func.id != "print":
            return False
        if not is_inside_function(node):
            return False
        # Hanya flag jika fungsi induknya juga punya return value.
        # Fungsi tanpa return yang berisi print() kemungkinan besar memang
        # fungsi output (tampilkan/cetak), bukan fungsi dengan sisa debug.
        parent_func = self._get_parent_func(node)
        return parent_func is not None and self._has_value_return(parent_func)

    @staticmethod
    def _get_parent_func(node):
        current = getattr(node, "_parent", None)
        while current is not None:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current
            current = getattr(current, "_parent", None)
        return None

    @staticmethod
    def _has_value_return(func_node):
        """True jika ada Return dengan nilai (bukan bare return) di fungsi ini."""
        for child in ast.walk(func_node):
            if child is func_node:
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False


class R10_NoReturn(PerNodeRule):
    rule_id = "R10_no_return"
    rule_name = "Fungsi melakukan komputasi tapi tidak ada return"
    severity = Severity.HIGH

    def condition(self, node, ctx):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        has_return = False
        has_computation = False
        has_print = False
        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(child, ast.Return):
                has_return = True
            if isinstance(child, (ast.Assign, ast.AugAssign, ast.For, ast.While)):
                has_computation = True
            if (isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == "print"):
                has_print = True
        # Jika fungsi mengeluarkan hasil via print(), besar kemungkinan
        # ia memang fungsi output yang tidak butuh return value.
        # Hanya flag R10 jika tidak ada print() sama sekali.
        if has_print:
            return False
        return has_computation and not has_return


class R11_HardcodedString(PerNodeRule):
    rule_id = "R11_hardcoded_string"
    rule_name = "String literal yang berulang (sebaiknya jadi konstanta)"
    severity = Severity.MEDIUM
    _SCRATCH_KEY = "_r11_flagged"

    def condition(self, node, ctx):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            return False
        if len(node.value) < 2:
            return False
        parent = getattr(node, "_parent", None)
        in_compare_or_assign = False
        while parent is not None:
            if isinstance(parent, (ast.Compare, ast.Assign)):
                in_compare_or_assign = True
                break
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.ClassDef, ast.Module)):
                break
            parent = getattr(parent, "_parent", None)
        if not in_compare_or_assign:
            return False
        if ctx.string_counts.get(node.value, 0) < 2:
            return False
        flagged: Set[str] = ctx.scratch.setdefault(self._SCRATCH_KEY, set())
        if node.value in flagged:
            return False
        flagged.add(node.value)
        return True


class R12_GlobalVariable(PerNodeRule):
    rule_id = "R12_global_variable"
    rule_name = "Penggunaan keyword `global` (merusak modularity)"
    severity = Severity.MEDIUM

    def condition(self, node, ctx):
        return isinstance(node, ast.Global)


class R13_EmptyExcept(PerNodeRule):
    rule_id = "R13_empty_except"
    rule_name = "Empty except (menyembunyikan error secara diam-diam)"
    severity = Severity.CRITICAL

    def condition(self, node, ctx):
        if not isinstance(node, ast.ExceptHandler):
            return False
        if len(node.body) != 1:
            return False
        return isinstance(node.body[0], ast.Pass)


class R14_InfiniteLoopRisk(PerNodeRule):
    rule_id = "R14_infinite_loop_risk"
    rule_name = "Risiko infinite loop (while True tanpa break)"
    severity = Severity.CRITICAL

    def condition(self, node, ctx):
        if not isinstance(node, ast.While):
            return False
        if not is_constant_true(node.test):
            return False
        return not has_break(node)


# ============================================================
# RULE R15 (global)
# ============================================================

class R15_CodeDuplication(GlobalRule):
    rule_id = "R15_code_duplication"
    rule_name = "Duplikasi kode (similarity >80% antar fungsi)"
    severity = Severity.HIGH
    THRESHOLD = 0.8
    MIN_BODY_LEN = 4

    def _body_signature(self, func: ast.FunctionDef) -> str:
        return "\n".join(
            ast.dump(stmt, annotate_fields=False) for stmt in func.body
        )

    def evaluate(self, ctx: AnalysisContext) -> List[Violation]:
        funcs: List[ast.FunctionDef] = [
            n for n in ctx.bfs_nodes
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and len(n.body) >= self.MIN_BODY_LEN
        ]
        violations: List[Violation] = []
        flagged: Set[int] = set()
        for f1, f2 in combinations(funcs, 2):
            sig1 = self._body_signature(f1)
            sig2 = self._body_signature(f2)
            ratio = difflib.SequenceMatcher(None, sig1, sig2).ratio()
            if ratio <= self.THRESHOLD:
                continue
            for f in (f1, f2):
                if id(f) in flagged:
                    continue
                flagged.add(id(f))
                violations.append(Violation(
                    rule_id=self.rule_id,
                    line_no=f.lineno,
                    severity=self.severity,
                    snippet=(f"def {f.name}(...):  "
                             f"# mirip dengan fungsi lain (ratio={ratio:.2f})"),
                    rule_name=self.rule_name,
                ))
        return violations


# ============================================================
# Knowledge Base
# ============================================================

class KnowledgeBase:
    """Kumpulan semua rules yang aktif."""

    def __init__(self):
        self.per_node_rules: List[PerNodeRule] = [
            R01_BareExcept(),
            R02_NonDescriptiveName(),
            R03_MissingDocstring(),
            R04_MagicNumber(),
            R05_DeepNesting(),
            R06_LongFunction(),
            R07_TooManyParams(),
            R08_MutableDefault(),
            R09_PrintDebug(),
            R10_NoReturn(),
            R11_HardcodedString(),
            R12_GlobalVariable(),
            R13_EmptyExcept(),
            R14_InfiniteLoopRisk(),
        ]
        self.global_rules: List[GlobalRule] = [
            R15_CodeDuplication(),
        ]

    @property
    def all_rules(self) -> List[Rule]:
        return list(self.per_node_rules) + list(self.global_rules)

    def __len__(self) -> int:
        return len(self.per_node_rules) + len(self.global_rules)

    def describe(self) -> List[dict]:
        return [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "severity": str(r.severity),
            }
            for r in self.all_rules
        ]
