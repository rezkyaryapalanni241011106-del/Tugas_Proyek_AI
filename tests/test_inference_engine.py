"""
test_inference_engine.py — Pengujian InferenceEngine (integrasi & perilaku engine).

Memverifikasi:
  - Engine berjalan pada kode bersih tanpa menghasilkan violations
  - SyntaxError dilempar untuk kode yang tidak valid
  - Violations terurut CRITICAL → HIGH → MEDIUM → LOW
  - Violation memiliki semua field yang diperlukan
  - summary() menghasilkan statistik yang benar
  - trace() menghasilkan log rule firings
  - KnowledgeBase memiliki tepat 15 rules

Author  : Kelompok AI Code Review Tutor (Testing & Evaluasi)
NIM     : 241011124 — Muhammad Akmal Ahsan
Course  : Kecerdasan Buatan, Semester Genap 2025/2026
"""

import pytest
from core.inference_engine import InferenceEngine
from core.knowledge_base import KnowledgeBase
from core.models import Severity

engine = InferenceEngine()

_SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}


# ═══════════════════════════════════════════════════════════════════════════
# Pengujian Dasar
# ═══════════════════════════════════════════════════════════════════════════
class TestInferenceEngineDasar:
    """Perilaku dasar inference engine."""

    def test_kode_bersih_tidak_ada_violations(self):
        """Kode bersih sesuai clean code → tidak boleh menghasilkan satu pun violation."""
        code = '''
def hitung_luas_persegi_panjang(panjang: float, lebar: float) -> float:
    """Menghitung luas persegi panjang."""
    return panjang * lebar


def gabung_nama(nama_depan: str, nama_belakang: str) -> str:
    """Menggabungkan nama depan dan nama belakang."""
    return nama_depan + nama_belakang
'''
        violations = engine.run(code)
        assert len(violations) == 0

    def test_syntax_error_dilempar(self):
        """Kode dengan syntax error Python → harus raise SyntaxError."""
        code = "def foo(:\n    pass"
        with pytest.raises(SyntaxError):
            engine.run(code)

    def test_kode_kosong_tidak_ada_violations(self):
        """String kosong → tidak menghasilkan violations."""
        violations = engine.run("")
        assert len(violations) == 0

    def test_violations_terurut_berdasarkan_severity(self):
        """Violations harus terurut: CRITICAL lebih dulu dari HIGH, dst."""
        code = """
skor = 0

def fungsi_buruk(items=[], data={}):
    global skor
    try:
        x = 1 / 0
    except:
        pass
    while True:
        skor += 1
"""
        violations = engine.run(code)
        assert len(violations) > 0
        orders = [_SEVERITY_ORDER[v.severity] for v in violations]
        assert orders == sorted(orders), "Violations tidak terurut berdasarkan severity"

    def test_violation_memiliki_semua_field(self):
        """Setiap Violation harus memiliki rule_id, rule_name, line_no, snippet, severity."""
        code = """
try:
    x = 1
except:
    pass
"""
        violations = engine.run(code)
        v = next((v for v in violations if v.rule_id == "R01_bare_except"), None)
        assert v is not None, "R01 seharusnya terdeteksi"
        assert v.rule_id
        assert v.rule_name
        assert v.line_no > 0
        assert v.snippet is not None
        assert isinstance(v.severity, Severity)

    def test_to_dict_serializable(self):
        """to_dict() harus menghasilkan dict yang bisa diserialisasi (JSON-safe)."""
        code = """
try:
    x = 1
except:
    pass
"""
        violations = engine.run(code)
        assert len(violations) > 0
        d = violations[0].to_dict()
        assert isinstance(d, dict)
        assert isinstance(d["severity"], str)
        assert isinstance(d["rule_id"], str)
        assert isinstance(d["line_no"], int)

    def test_run_menghasilkan_list(self):
        """run() selalu mengembalikan list (bisa kosong)."""
        result = engine.run("x = 1")
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════════════════
# Pengujian summary()
# ═══════════════════════════════════════════════════════════════════════════
class TestSummary:
    """Metode summary() pada InferenceEngine."""

    def test_total_sama_dengan_jumlah_violations(self):
        """summary['total'] harus sama dengan len(violations)."""
        code = """
a = 10
b = 20
try:
    x = 1
except:
    pass
"""
        violations = engine.run(code)
        summary = engine.summary(violations)
        assert summary["total"] == len(violations)

    def test_by_severity_memiliki_empat_kunci(self):
        """by_severity harus memiliki kunci CRITICAL, HIGH, MEDIUM, LOW."""
        violations = engine.run("x = 1")
        summary = engine.summary(violations)
        assert set(summary["by_severity"].keys()) == {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

    def test_by_severity_count_akurat(self):
        """Jumlah per severity dalam summary harus akurat."""
        code = """
try:
    x = 1
except:
    pass
while True:
    x += 1
"""
        violations = engine.run(code)
        summary = engine.summary(violations)
        critical_from_summary = summary["by_severity"]["CRITICAL"]
        critical_actual = sum(1 for v in violations if v.severity == Severity.CRITICAL)
        assert critical_from_summary == critical_actual

    def test_by_rule_mencatat_rule_id(self):
        """by_rule harus mencantumkan rule_id yang sesuai."""
        code = """
try:
    x = 1
except:
    pass
"""
        violations = engine.run(code)
        summary = engine.summary(violations)
        assert "R01_bare_except" in summary["by_rule"]

    def test_summary_kode_bersih(self):
        """Kode bersih → semua summary count harus nol."""
        violations = engine.run('')
        summary = engine.summary(violations)
        assert summary["total"] == 0
        assert all(v == 0 for v in summary["by_severity"].values())


# ═══════════════════════════════════════════════════════════════════════════
# Pengujian trace()
# ═══════════════════════════════════════════════════════════════════════════
class TestTrace:
    """Metode trace() pada InferenceEngine."""

    def test_trace_mengembalikan_dict(self):
        """trace() harus mengembalikan dict dengan kunci yang benar."""
        result = engine.trace("x = 1")
        assert isinstance(result, dict)
        assert "ast_node_count" in result
        assert "rule_firings" in result

    def test_trace_ast_node_count_lebih_dari_nol(self):
        """ast_node_count harus > 0 untuk kode non-kosong."""
        trace = engine.trace("x = 1 + 2")
        assert trace["ast_node_count"] > 0

    def test_trace_rule_firings_mencatat_rule_id(self):
        """rule_firings harus mencantumkan rule_id yang fired."""
        code = """
try:
    x = 1
except:
    pass
"""
        trace = engine.trace(code)
        fired_ids = [f["rule_id"] for f in trace["rule_firings"]]
        assert "R01_bare_except" in fired_ids

    def test_trace_kode_bersih_tidak_ada_firings(self):
        """Kode bersih → rule_firings harus kosong."""
        code = '''
def hitung(angka_pertama: int, angka_kedua: int) -> int:
    """Menjumlahkan dua angka."""
    return angka_pertama + angka_kedua
'''
        trace = engine.trace(code)
        assert trace["rule_firings"] == []

    def test_trace_firing_memiliki_field_lengkap(self):
        """Setiap entry firing harus punya node_type, line_no, rule_id, rule_name."""
        code = """
try:
    pass
except:
    pass
"""
        trace = engine.trace(code)
        assert len(trace["rule_firings"]) > 0
        for firing in trace["rule_firings"]:
            assert "node_type" in firing
            assert "rule_id" in firing
            assert "rule_name" in firing


# ═══════════════════════════════════════════════════════════════════════════
# Pengujian KnowledgeBase
# ═══════════════════════════════════════════════════════════════════════════
class TestKnowledgeBase:
    """Memastikan KnowledgeBase memuat tepat 15 rules yang lengkap."""

    def test_kb_memiliki_tepat_15_rules(self):
        """Sesuai proposal: harus ada tepat 15 rules aktif."""
        kb = KnowledgeBase()
        assert len(kb) == 15

    def test_semua_rule_id_hadir(self):
        """Semua rule_id dari R01 hingga R15 harus ada di KnowledgeBase."""
        kb = KnowledgeBase()
        ids = {r.rule_id for r in kb.all_rules}
        expected = {
            "R01_bare_except",
            "R02_non_descriptive_name",
            "R03_missing_docstring",
            "R04_magic_number",
            "R05_deep_nesting",
            "R06_long_function",
            "R07_too_many_params",
            "R08_mutable_default",
            "R09_print_debug",
            "R10_no_return",
            "R11_hardcoded_string",
            "R12_global_variable",
            "R13_empty_except",
            "R14_infinite_loop_risk",
            "R15_code_duplication",
        }
        assert ids == expected

    def test_kb_describe_mengembalikan_15_item(self):
        """describe() harus mengembalikan list dengan 15 item."""
        kb = KnowledgeBase()
        desc = kb.describe()
        assert isinstance(desc, list)
        assert len(desc) == 15

    def test_kb_describe_field_lengkap(self):
        """Setiap item describe() harus punya rule_id, rule_name, severity."""
        kb = KnowledgeBase()
        for item in kb.describe():
            assert "rule_id" in item
            assert "rule_name" in item
            assert "severity" in item

    def test_engine_default_menggunakan_kb_lengkap(self):
        """InferenceEngine tanpa argumen harus menggunakan KnowledgeBase penuh."""
        eng = InferenceEngine()
        assert len(eng.kb) == 15
