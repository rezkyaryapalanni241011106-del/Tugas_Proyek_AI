"""
main.py — CLI runner untuk AI Code Review Tutor.

Cara pakai (dari root project):
    python main.py                          # default: analisis samples/sample_bad_code.py
    python main.py path/to/file.py          # analisis file lain
    python main.py path/to/file.py --json   # output JSON (integrasi LLM/UI)
    python main.py path/to/file.py --trace  # trace rule firings (untuk demo)
    python main.py --rules                  # print metadata semua rules
    python main.py --no-color               # disable ANSI color output

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
"""

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.inference_engine import InferenceEngine
from core.knowledge_base import KnowledgeBase
from core.llm_explainer import generate_feedback


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    RED = "\033[31m"; YELLOW = "\033[33m"; BLUE = "\033[34m"
    MAGENTA = "\033[35m"; CYAN = "\033[36m"; GREEN = "\033[32m"

    @classmethod
    def disable(cls):
        for name in ("RESET", "BOLD", "DIM", "RED", "YELLOW",
                     "BLUE", "MAGENTA", "CYAN", "GREEN"):
            setattr(cls, name, "")


SEVERITY_COLOR = {
    "CRITICAL": lambda: C.RED + C.BOLD,
    "HIGH":     lambda: C.RED,
    "MEDIUM":   lambda: C.YELLOW,
    "LOW":      lambda: C.BLUE,
}


def pretty_print(violations, summary: dict, source_path: Path) -> None:
    print()
    print(C.BOLD + "=" * 72 + C.RESET)
    print(C.BOLD + "  AI CODE REVIEW TUTOR — Hasil Analisis Rule Engine".ljust(72) + C.RESET)
    print(C.BOLD + "=" * 72 + C.RESET)
    print()
    print(f"  File          : {C.CYAN}{source_path}{C.RESET}")
    print(f"  Total issues  : {C.BOLD}{summary['total']}{C.RESET}")
    print()
    print(f"  {C.BOLD}Distribusi by severity:{C.RESET}")
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        count = summary["by_severity"].get(sev, 0)
        if count == 0:
            continue
        color = SEVERITY_COLOR[sev]()
        bar = "█" * min(count, 30)
        print(f"    {color}{sev:9s}{C.RESET}  {count:3d}  {C.DIM}{bar}{C.RESET}")
    print()
    print(C.BOLD + "-" * 72 + C.RESET)
    print()
    if not violations:
        print(f"  {C.GREEN}✓ Tidak ada antipattern terdeteksi pada kode ini.{C.RESET}")
        print()
        return
    for i, v in enumerate(violations, 1):
        color = SEVERITY_COLOR[v.severity.name]()
        print(f"  {C.BOLD}#{i:2d}{C.RESET}  "
              f"{color}[{v.severity.name:8s}]{C.RESET}  "
              f"{C.CYAN}{v.rule_id}{C.RESET}  "
              f"{C.DIM}(line {v.line_no}){C.RESET}")
        print(f"       {C.BOLD}{v.rule_name}{C.RESET}")
        for line in v.snippet.splitlines():
            print(f"       {C.DIM}│{C.RESET} {line}")
        print()


def print_rules_catalog(kb: KnowledgeBase) -> None:
    print()
    print(C.BOLD + f"Knowledge Base — {len(kb)} Rules" + C.RESET)
    print(C.BOLD + "-" * 72 + C.RESET)
    for r in kb.describe():
        color = SEVERITY_COLOR[r["severity"]]()
        print(f"  {C.CYAN}{r['rule_id']:30s}{C.RESET}  "
              f"{color}[{r['severity']:8s}]{C.RESET}  {r['rule_name']}")
    print()


def main() -> int:
    args = sys.argv[1:]
    json_output  = "--json"     in args
    trace_output = "--trace"    in args
    show_rules   = "--rules"    in args
    no_color     = "--no-color" in args

    if no_color or not sys.stdout.isatty():
        C.disable()

    positional = [a for a in args if not a.startswith("--")]
    kb = KnowledgeBase()

    if show_rules:
        print_rules_catalog(kb)
        return 0

    target = Path(positional[0]) if positional else (
        Path(__file__).parent / "samples" / "sample_bad_code.py"
    )
    if not target.exists():
        print(f"Error: file tidak ditemukan: {target}", file=sys.stderr)
        return 1

    source = target.read_text(encoding="utf-8")
    engine = InferenceEngine(kb)

    try:
        violations = engine.run(source)
    except SyntaxError as e:
        print(f"Error: syntax error di line {e.lineno}: {e.msg}", file=sys.stderr)
        return 2

    summary = engine.summary(violations)

    if trace_output:
        print(json.dumps(engine.trace(source), indent=2, ensure_ascii=False))
        return 0

    if json_output:
        list_pelanggaran = [v.to_dict() for v in violations]
        print(f"\nMemulai proses LLM untuk {len(list_pelanggaran)} pelanggaran...",
              file=sys.stderr)
        hasil_llm, llm_status, llm_provider = generate_feedback(list_pelanggaran)
        out = {
            "source_file": str(target),
            "summary": summary,
            "llm_provider": llm_provider,
            "llm_status": llm_status,
            "feedback_edukatif": hasil_llm,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    pretty_print(violations, summary, target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
