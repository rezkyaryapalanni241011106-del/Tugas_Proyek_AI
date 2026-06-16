"""
llm_explainer.py — Generator feedback edukatif berbasis LLM.

Modul ini PROVIDER-AGNOSTIC: ia hanya menyusun prompt, memanggil penyedia
aktif lewat `core.llm_providers`, lalu mem-parse hasilnya. Penyedia mana
yang dipakai (Groq/OpenAI/Gemini/Claude/DeepSeek) ditentukan di .env via
`LLM_PROVIDER` — lihat core/llm_providers.py.

Strategi penting:
  • Satu panggilan batch  → seluruh rule unik dikirim sekaligus (bukan satu
    panggilan per rule), jadi prosesnya ~2-4 detik, bukan N×.
  • Tidak ada cap rule     → SEMUA rule yang terdeteksi mendapat penjelasan
    dari LLM (selama tidak kena rate limit), bukan hanya sebagian.
  • Cache in-memory per (provider, rule_id) → penjelasan R01 sama untuk semua
    kode yang melanggar R01, jadi aman dipakai ulang. Request ke-2, ke-3, dst.
    tetap mendapat penjelasan AI tanpa memanggil ulang LLM (hemat token &
    menghindari rate limit). Cache di-key per provider agar tidak tercampur
    bila penyedia diganti.

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
Penanggung jawab modul ini: Habel Mangopo
"""

import json
import os
import re
import sys

from dotenv import load_dotenv

from .llm_providers import (
    LLMProvider,
    ProviderAuthError,
    ProviderConnectionError,
    ProviderError,
    ProviderNotInstalled,
    ProviderRateLimit,
    resolve_provider,
)

load_dotenv()

# Batas aman jumlah rule baru per panggilan. Knowledge base hanya punya 15
# rule, dan violations sudah dideduplikasi per rule_id di backend, jadi nilai
# ini efektif "tanpa batas" — TUJUANNYA agar SEMUA rule yang terdeteksi
# benar-benar dapat penjelasan dari LLM dalam satu panggilan.
MAX_RULES_PER_CALL = 30

# Cache in-memory: "provider:rule_id" → hasil_llm dict.
_rule_cache: dict = {}


# ============================================================
# Prompt
# ============================================================

_SYSTEM_PROMPT = (
    "Kamu adalah asisten dosen pemrograman dasar yang suportif dan proporsional. "
    "Selalu kembalikan respons HANYA dalam bentuk JSON valid sesuai instruksi, "
    "tanpa teks tambahan di luar JSON."
)


def meracik_prompt_batch(v_star_list: list) -> str:
    """Susun satu prompt yang memuat seluruh violation sekaligus."""
    violations_str = json.dumps(v_star_list, ensure_ascii=False, indent=2)
    return f"""
Berikut daftar kebiasaan kode yang perlu diperbaiki, ditemukan dalam kode
mahasiswa tingkat DASAR (format JSON):

{violations_str}

KONTEKS PENTING sebelum memberi feedback:
- Ini kode mahasiswa yang BARU belajar Python (semester 1-2).
- Tujuanmu MENDIDIK, bukan menghakimi. Nada memotivasi, jangan bikin patah semangat.
- Sesuaikan bobot penjelasan dengan severity: CRITICAL/HIGH butuh penjelasan
  serius; MEDIUM/LOW cukup singkat dan ringan.
- Jangan dramatis untuk masalah kecil (LOW/MEDIUM).

Berikan feedback edukatif dalam Bahasa Indonesia untuk SETIAP item di atas.

PENTING soal format keluaran:
- Kembalikan SATU objek JSON dengan key "feedback" berisi array.
- Array harus berisi tepat {len(v_star_list)} objek, urutannya sama dengan input.
- Gunakan persis struktur ini:

{{
  "feedback": [
    {{
      "rule_id": "salin rule_id dari input",
      "penjelasan": "penjelasan singkat mengapa kebiasaan ini perlu diperbaiki (proporsional dengan severity)",
      "kode_perbaikan": "contoh kode Python yang sudah diperbaiki",
      "latihan": "satu soal latihan singkat"
    }}
  ]
}}
"""


# ============================================================
# Parsing respons (longgar — tahan terhadap variasi antar provider)
# ============================================================

def _extract_items(raw: str) -> list:
    """Ekstrak list objek feedback dari teks mentah respons LLM.

    Tahan terhadap: pembungkus markdown ```json, objek pembungkus
    {"feedback": [...]}, atau array telanjang [...].
    """
    text = (raw or "").strip()
    if not text:
        return []

    # Buang pembungkus code fence bila ada
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

    parsed = _try_json(text)
    if parsed is None:
        # Coba ambil substring array [...] lalu objek {...}
        m = re.search(r"\[.*\]", text, re.S)
        if m:
            parsed = _try_json(m.group(0))
        if parsed is None:
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                parsed = _try_json(m.group(0))
    if parsed is None:
        return []

    return _coerce_list(parsed)


def _try_json(s: str):
    try:
        return json.loads(s)
    except Exception:
        return None


def _coerce_list(parsed) -> list:
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        # Prioritaskan key "feedback"; jika tidak ada, ambil list pertama.
        if isinstance(parsed.get("feedback"), list):
            return parsed["feedback"]
        for v in parsed.values():
            if isinstance(v, list):
                return v
        return [parsed]   # satu objek tunggal
    return []


def _normalize(items: list) -> list:
    """Ubah item mentah menjadi struktur {rule_id, hasil_llm} yang konsisten."""
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append({
            "rule_id": item.get("rule_id", ""),
            "hasil_llm": {
                "penjelasan":     item.get("penjelasan", ""),
                "kode_perbaikan": item.get("kode_perbaikan", ""),
                "latihan":        item.get("latihan", ""),
            },
        })
    return out


def _call_provider(provider: LLMProvider, batch: list) -> list:
    """Satu panggilan ke penyedia aktif; kembalikan list hasil ternormalisasi."""
    raw = provider.chat_json(_SYSTEM_PROMPT, meracik_prompt_batch(batch))
    return _normalize(_extract_items(raw))


# ============================================================
# API publik
# ============================================================

def generate_feedback(v_star_list: list):
    """Hasilkan feedback edukatif untuk violations via penyedia LLM aktif.

    Args:
        v_star_list: list dict violation (hasil Violation.to_dict()), idealnya
                     sudah dideduplikasi per rule_id oleh pemanggil.

    Returns:
        Tuple (results, status, provider_label):
          results        — list dict {rule_id, hasil_llm}
          status         — "ok" | "rate_limited" | "no_key" | "error"
          provider_label — nama tampilan penyedia aktif (mis. "Groq"),
                           untuk ditampilkan di UI / pesan diagnostik
    """
    if not v_star_list:
        return [], "ok", ""

    provider, pstatus, label = resolve_provider()

    if provider is None:
        if pstatus == "unknown_provider":
            print(f"  ! LLM_PROVIDER '{label}' tidak dikenal — periksa .env "
                  f"(pilih: groq/openai/gemini/claude/deepseek).", file=sys.stderr)
            return [], "no_key", label or "?"
        # no_key
        print(f"  ! API key untuk penyedia '{label}' belum diisi di .env — "
              f"analisis berjalan dengan penjelasan umum.", file=sys.stderr)
        return [], "no_key", label

    pname = provider.name

    # Pisahkan: sudah di-cache vs perlu panggil LLM
    cached_results = []
    need_llm = []
    for v in v_star_list:
        rid = v.get("rule_id", "")
        ckey = f"{pname}:{rid}"
        if ckey in _rule_cache:
            cached_results.append({"rule_id": rid, "hasil_llm": _rule_cache[ckey]})
        else:
            need_llm.append(v)

    if cached_results:
        print(f"  ✦ [{label}] cache hit {len(cached_results)} rule, "
              f"{len(need_llm)} rule perlu LLM.", file=sys.stderr)

    if not need_llm:
        print(f"  ✦ [{label}] semua dari cache — LLM tidak dipanggil.",
              file=sys.stderr)
        return cached_results, "ok", label

    batch = need_llm[:MAX_RULES_PER_CALL]
    print(f"  ✦ [{label}] mengirim {len(batch)} rule ke {provider.model} ...",
          file=sys.stderr)

    try:
        new_results = _call_provider(provider, batch)

        for r in new_results:
            rid = r.get("rule_id", "")
            if rid:
                _rule_cache[f"{pname}:{rid}"] = r["hasil_llm"]

        print(f"  ✦ [{label}] selesai: {len(new_results)} hasil baru "
              f"(cache total {len(_rule_cache)}).", file=sys.stderr)
        return cached_results + new_results, "ok", label

    except ProviderRateLimit:
        print(f"  ! [{label}] rate limit — kuota per menit habis.", file=sys.stderr)
        if cached_results:
            return cached_results, "ok", label
        return [], "rate_limited", label

    except ProviderAuthError:
        print(f"  ! [{label}] API key tidak valid — periksa .env.", file=sys.stderr)
        return cached_results, "error", label

    except ProviderNotInstalled as e:
        print(f"  ! [{label}] SDK belum terpasang: {e}", file=sys.stderr)
        return cached_results, "error", label

    except ProviderConnectionError as e:
        print(f"  ! [{label}] koneksi gagal: {e}", file=sys.stderr)
        return cached_results, "error", label

    except ProviderError as e:
        print(f"  ! [{label}] error tak terduga: {e}", file=sys.stderr)
        return cached_results, "error", label
