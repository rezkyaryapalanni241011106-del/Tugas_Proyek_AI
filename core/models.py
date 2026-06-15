"""
models.py — Struktur data inti untuk AI Code Review Tutor.

Mendefinisikan:
- Severity: enum tingkat keparahan (CRITICAL > HIGH > MEDIUM > LOW)
- Violation: representasi sebuah pelanggaran rule yang dideteksi

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
"""

from dataclasses import dataclass, asdict
from enum import Enum


class Severity(Enum):
    """Tingkat keparahan sebuah antipattern."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

    def __str__(self) -> str:
        return self.name


@dataclass
class Violation:
    """Sebuah antipattern yang berhasil dideteksi rule engine."""
    rule_id: str
    line_no: int
    severity: Severity
    snippet: str
    rule_name: str

    def to_dict(self) -> dict:
        """Konversi ke dict JSON-serializable."""
        d = asdict(self)
        d["severity"] = str(self.severity)
        return d

    def __str__(self) -> str:
        return (f"[{self.severity}] {self.rule_id} "
                f"(line {self.line_no}): {self.rule_name}")
