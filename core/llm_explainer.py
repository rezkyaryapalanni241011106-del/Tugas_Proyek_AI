"""
llm_explainer.py — LLM Feedback Generator menggunakan Groq.

Mengirim SEMUA violations dalam satu panggilan API (batch) agar
proses selesai dalam ~2-4 detik, bukan N × sleep detik.

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
Penanggung jawab modul ini: Habel Mangopo
"""

import json
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from groq import Groq


def meracik_prompt_batch(v_star_list: list) -> str:
    """Susun satu prompt yang memuat SEMUA violations sekaligus."""
    violations_str = json.dumps(v_star_list, ensure_ascii=False, indent=2)
    return f"""
Kamu adalah asisten dosen pemrograman dasar yang ramah.
Berikut adalah daftar antipattern yang ditemukan dalam kode mahasiswa (format JSON):

{violations_str}

Berikan feedback edukatif dalam Bahasa Indonesia untuk SETIAP antipattern di atas.

PENTING: Kembalikan HANYA JSON array yang valid dengan tepat {len(v_star_list)} objek.
Urutan objek harus sama dengan urutan input. Gunakan persis struktur berikut:
[
  {{
    "rule_id": "salin rule_id dari input",
    "penjelasan": "penjelasan singkat mengapa kebiasaan ini buruk",
    "kode_perbaikan": "contoh kode Python yang sudah diperbaiki",
    "latihan": "satu soal latihan singkat"
  }}
]
"""


def generate_feedback(v_star_list: list) -> list:
    """Hasilkan feedback edukatif untuk semua violations via satu panggilan Groq.

    Args:
        v_star_list: list dict violation dari rule engine (hasil to_dict()).

    Returns:
        list dict berisi rule_id dan hasil_llm (atau [] jika API gagal).
    """
    if not v_star_list:
        return []

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        print("Info: GROQ_API_KEY belum diisi. Analisis berjalan tanpa LLM.", file=sys.stderr)
        return []

    client = Groq(api_key=api_key)

    print(f"  ✦ Mengirim {len(v_star_list)} violations ke Groq (batch)...", file=sys.stderr)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Kamu adalah asisten dosen pemrograman dasar. Selalu kembalikan respons dalam format JSON array yang valid.",
                },
                {
                    "role": "user",
                    "content": meracik_prompt_batch(v_star_list),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )

        raw = response.choices[0].message.content
        parsed = json.loads(raw)

        # Groq dengan json_object kadang membungkus array dalam key
        if isinstance(parsed, dict):
            results = next(
                (v for v in parsed.values() if isinstance(v, list)),
                list(parsed.values()),
            )
        else:
            results = parsed

        if not isinstance(results, list):
            results = [results]

        return [
            {
                "rule_id": item.get("rule_id", ""),
                "hasil_llm": {
                    "penjelasan":     item.get("penjelasan", ""),
                    "kode_perbaikan": item.get("kode_perbaikan", ""),
                    "latihan":        item.get("latihan", ""),
                },
            }
            for item in results
        ]

    except Exception as e:
        print(f"  ! Error Groq batch: {e}", file=sys.stderr)
        return []
