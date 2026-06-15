"""
inference_engine.py — Forward Chaining Inference Engine.

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
Penanggung jawab modul ini: Andi Ahmad Naufal Madani (NIM 241011128)
"""

from typing import List, Optional

from .models import Severity, Violation
from .parser import parse_source, attach_parents, AnalysisContext
from .knowledge_base import KnowledgeBase


_SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}


class InferenceEngine:
    """Forward chaining inference engine."""

    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        self.kb: KnowledgeBase = knowledge_base or KnowledgeBase()

    def run(self, source_code: str) -> List[Violation]:
        """Eksekusi forward chaining atas source code.

        Returns:
            List[Violation] terurut dari paling parah (CRITICAL) ke paling
            ringan (LOW).

        Raises:
            SyntaxError: jika kode mengandung syntax error.
        """
        tree = parse_source(source_code)
        attach_parents(tree)
        ctx = AnalysisContext(source_code, tree)

        violations: List[Violation] = []

        for node in ctx.bfs_nodes:
            for rule in self.kb.per_node_rules:
                if rule.condition(node, ctx):
                    violations.append(rule.make_violation(node, ctx))

        for grule in self.kb.global_rules:
            violations.extend(grule.evaluate(ctx))

        violations.sort(
            key=lambda v: (_SEVERITY_ORDER[v.severity], v.line_no)
        )

        return violations

    def summary(self, violations: List[Violation]) -> dict:
        """Hasilkan ringkasan statistik dari hasil run()."""
        by_severity = {sev.name: 0 for sev in Severity}
        by_rule: dict = {}
        for v in violations:
            by_severity[v.severity.name] += 1
            by_rule[v.rule_id] = by_rule.get(v.rule_id, 0) + 1
        return {
            "total": len(violations),
            "by_severity": by_severity,
            "by_rule": by_rule,
        }

    def trace(self, source_code: str) -> dict:
        """Hasilkan log rule firings untuk demo/dokumentasi."""
        tree = parse_source(source_code)
        attach_parents(tree)
        ctx = AnalysisContext(source_code, tree)

        firings = []
        for node in ctx.bfs_nodes:
            for rule in self.kb.per_node_rules:
                if rule.condition(node, ctx):
                    firings.append({
                        "node_type": type(node).__name__,
                        "line_no": getattr(node, "lineno", None),
                        "rule_id": rule.rule_id,
                        "rule_name": rule.rule_name,
                    })
        for grule in self.kb.global_rules:
            for v in grule.evaluate(ctx):
                firings.append({
                    "node_type": "(global)",
                    "line_no": v.line_no,
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                })

        return {
            "ast_node_count": len(ctx.bfs_nodes),
            "rule_firings": firings,
        }
