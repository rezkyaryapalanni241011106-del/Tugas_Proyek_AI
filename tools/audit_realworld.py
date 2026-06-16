"""
audit_realworld.py — Uji "kode nyata" terhadap pipeline analisis.

Menjalankan ~200 program Python realistis (lihat tests/realworld_corpus.py)
melalui pipeline /api/analyze YANG SESUNGGUHNYA (tanpa API key → rule engine
+ penjelasan fallback), lalu memeriksa:

  1. ROBUSTNESS (hard): tidak ada crash; response well-formed; setiap violation
     punya explanation + fixed_code + source non-kosong; kode syntax-error → 422.
  2. FALSE POSITIVE (hard): rule yang ada di `forbid` TIDAK boleh muncul.
  3. FALSE NEGATIVE (hard): rule yang ada di `expect` HARUS muncul.
  4. EXTRA (info): deteksi di luar `expect` — dilaporkan untuk ditinjau manual
     (biasanya rule "agresif" seperti R03/R04/R11 yang memang sesuai desain).

Cara pakai (dari root project):
    python tools/audit_realworld.py            # ringkas
    python tools/audit_realworld.py --verbose  # tampilkan tiap mismatch
"""

import os
import sys
from pathlib import Path

# Pastikan root project ada di sys.path & tidak ada API key (paksa jalur fallback)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
for k in ("GROQ_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
          "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"):
    os.environ.pop(k, None)
os.environ["LLM_PROVIDER"] = "groq"  # tak ada key → status no_key, pakai fallback

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient

import app
from core.inference_engine import InferenceEngine
from tests.realworld_corpus import SAMPLES

VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv

REQUIRED_FIELDS = ("rule_id", "rule_name", "severity", "line_no",
                   "snippet", "explanation", "fixed_code", "source")
VALID_SOURCES = {"ai", "fallback"}
VALID_SEV = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


def check_wellformed(data: dict) -> list:
    """Kembalikan daftar masalah struktur pada response /api/analyze (kosong = OK)."""
    problems = []
    if "violations" not in data or not isinstance(data["violations"], list):
        return ["response tidak punya list 'violations'"]
    for i, v in enumerate(data["violations"]):
        for f in REQUIRED_FIELDS:
            if f not in v:
                problems.append(f"violation[{i}] tidak punya field '{f}'")
        if v.get("source") not in VALID_SOURCES:
            problems.append(f"violation[{i}] source tidak valid: {v.get('source')!r}")
        if v.get("severity") not in VALID_SEV:
            problems.append(f"violation[{i}] severity tidak valid: {v.get('severity')!r}")
        if not str(v.get("explanation", "")).strip():
            problems.append(f"violation[{i}] ({v.get('rule_id')}) explanation KOSONG")
        if not str(v.get("fixed_code", "")).strip():
            problems.append(f"violation[{i}] ({v.get('rule_id')}) fixed_code KOSONG")
    for f in ("summary", "llm_status", "llm_used", "llm_provider"):
        if f not in data:
            problems.append(f"response tidak punya field '{f}'")
    return problems


def main() -> int:
    client = TestClient(app.app)
    engine = InferenceEngine()

    total = len(SAMPLES)
    n_pass = 0
    failures = []          # (name, list-of-reasons)
    extras_by_rule = {}    # rule_id -> count of "extra" detections
    detect_tally = {}      # rule_id -> berapa sampel mendeteksinya
    fp_by_rule = {}        # rule_id -> count false positive
    fn_by_rule = {}        # rule_id -> count false negative
    n_syntax = 0
    n_clean_expected = 0   # sampel tanpa expect (harusnya minim/0 deteksi serius)

    for s in SAMPLES:
        name = s["name"]
        code = s["code"]
        expect = set(s.get("expect", ()))
        forbid = set(s.get("forbid", ()))
        want_syntax = s.get("syntax_error", False)
        reasons = []

        # ---- Jalur syntax-error ----
        if want_syntax:
            n_syntax += 1
            engine_raised = False
            try:
                engine.run(code)
            except SyntaxError:
                engine_raised = True
            except Exception as e:
                reasons.append(f"engine.run melempar {type(e).__name__} (harusnya SyntaxError): {e}")
            if not engine_raised and not reasons:
                reasons.append("engine TIDAK mendeteksi SyntaxError pada kode rusak")

            r = client.post("/api/analyze", json={"code": code})
            if r.status_code != 422:
                reasons.append(f"/api/analyze status {r.status_code} (harusnya 422)")
            else:
                detail = r.json().get("detail", "")
                if "Syntax error" not in detail:
                    reasons.append(f"detail 422 tidak menyebut syntax error: {detail!r}")

            if reasons:
                failures.append((name, reasons))
            else:
                n_pass += 1
            continue

        # ---- Jalur kode valid ----
        try:
            violations = engine.run(code)
        except SyntaxError as e:
            failures.append((name, [f"kode VALID tapi engine melempar SyntaxError: baris {e.lineno}: {e.msg}"]))
            continue
        except Exception as e:
            failures.append((name, [f"engine.run crash: {type(e).__name__}: {e}"]))
            continue

        detected = {v.rule_id for v in violations}
        for rid in detected:
            detect_tally[rid] = detect_tally.get(rid, 0) + 1

        # API harus konsisten & well-formed
        r = client.post("/api/analyze", json={"code": code})
        if r.status_code != 200:
            reasons.append(f"/api/analyze status {r.status_code} (harusnya 200): {r.text[:120]}")
        else:
            data = r.json()
            api_rules = {v["rule_id"] for v in data.get("violations", [])}
            if api_rules != detected:
                reasons.append(f"deteksi API {sorted(api_rules)} != engine {sorted(detected)}")
            reasons.extend(check_wellformed(data))

        # False negative (expect tapi tak terdeteksi)
        missing = expect - detected
        for rid in missing:
            fn_by_rule[rid] = fn_by_rule.get(rid, 0) + 1
        if missing:
            reasons.append(f"FALSE NEGATIVE — diharapkan tapi tak terdeteksi: {sorted(missing)}")

        # False positive (forbid tapi terdeteksi)
        fp = forbid & detected
        for rid in fp:
            fp_by_rule[rid] = fp_by_rule.get(rid, 0) + 1
        if fp:
            reasons.append(f"FALSE POSITIVE — terlarang tapi terdeteksi: {sorted(fp)}")

        # Extra (info saja)
        extra = detected - expect
        for rid in extra:
            extras_by_rule[rid] = extras_by_rule.get(rid, 0) + 1

        if not expect:
            n_clean_expected += 1

        if reasons:
            failures.append((name, reasons))
        else:
            n_pass += 1

    # ================= LAPORAN =================
    print("=" * 74)
    print("  AUDIT KODE NYATA — Hasil")
    print("=" * 74)
    print(f"  Total sampel        : {total}")
    print(f"    • kode valid      : {total - n_syntax}")
    print(f"    • syntax error     : {n_syntax}")
    print(f"  LULUS (hard checks) : {n_pass}/{total}")
    print(f"  GAGAL               : {len(failures)}")
    print()

    print("  Tally deteksi per rule (berapa sampel memicunya):")
    for rid in sorted(detect_tally):
        print(f"    {rid:28s} {detect_tally[rid]:3d}")
    rules_never = [f"R{n:02d}" for n in range(1, 16)]
    fired_prefixes = {rid.split('_')[0] for rid in detect_tally}
    never = [p for p in rules_never if p not in fired_prefixes]
    if never:
        print(f"    (tidak pernah terpicu: {', '.join(never)})")
    print()

    if fp_by_rule:
        print("  ⚠ FALSE POSITIVE per rule (forbid tapi muncul):")
        for rid in sorted(fp_by_rule):
            print(f"    {rid:28s} {fp_by_rule[rid]:3d}")
        print()
    if fn_by_rule:
        print("  ⚠ FALSE NEGATIVE per rule (expect tapi hilang):")
        for rid in sorted(fn_by_rule):
            print(f"    {rid:28s} {fn_by_rule[rid]:3d}")
        print()

    if extras_by_rule:
        print("  ℹ Deteksi EXTRA di luar `expect` (tinjau manual — mungkin agresif tapi valid):")
        for rid in sorted(extras_by_rule):
            print(f"    {rid:28s} {extras_by_rule[rid]:3d}")
        print()

    if failures:
        print("-" * 74)
        print(f"  RINCIAN {len(failures)} KEGAGALAN:")
        shown = failures if VERBOSE else failures[:40]
        for name, reasons in shown:
            print(f"\n  ✗ {name}")
            for r in reasons:
                print(f"      - {r}")
        if not VERBOSE and len(failures) > 40:
            print(f"\n  ... {len(failures) - 40} kegagalan lagi (pakai --verbose untuk semua)")
        print()

    print("=" * 74)
    ok = len(failures) == 0
    print("  HASIL AKHIR:", "✓ SEMUA LULUS" if ok else f"✗ {len(failures)} GAGAL")
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
