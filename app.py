"""
app.py — FastAPI Server untuk AI Code Review Tutor.

Menggabungkan static file serving + REST API:
  GET  /api/samples/{key}  → Kembalikan kode contoh (basic/magic/deep/all)
  POST /api/analyze        → Jalankan rule engine + Gemini, kembalikan violations
  GET  /api/rules          → Metadata semua 15 rules
  GET  /                   → Sajikan index.html (frontend)

Cara menjalankan (dari folder project):
  pip install -r requirements.txt
  set GROQ_API_KEY=gsk_...            (Windows, opsional — tanpa ini fallback dipakai)
  uvicorn app:app --port 8000

  Catatan: JANGAN pakai --reload untuk penggunaan normal. --reload membuat
  server RESTART setiap ada file yang berubah (mis. editor auto-save), sehingga
  sesi bisa terputus di tengah jalan. Pakai --reload hanya saat mengembangkan kode.

Buka browser: http://localhost:8000

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.inference_engine import InferenceEngine
from core.knowledge_base import KnowledgeBase
from core.llm_explainer import generate_feedback

# Paksa UTF-8 di terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

app = FastAPI(title="AI Code Review Tutor", version="1.0.0", docs_url="/docs")

# ============================================================
# Data contoh kode — dipindahkan dari script.js ke sini
# ============================================================
SAMPLES: dict[str, str] = {
    "basic": """\
# Kode dengan beberapa antipattern pemrograman dasar
def h(x, y, z):
    try:
        r = x / y
        if z > 0:
            if r > 0:
                if z > 10:
                    print("hasil:", r * 365)
                else:
                    print("kecil")
        return r
    except:
        pass

def hitung_gaji(g, b, p, t, i, l):
    total = g + b + p + t + i + l
    print(total)
""",
    "magic": """\
# Contoh magic number dan hardcoded string
def proses_nilai(n):
    if n >= 80:
        status = "lulus"
    elif n >= 60:
        status = "cukup"
    else:
        status = "tidak lulus"
    pajak = n * 0.11
    hasil = n * 365 * 24
    print(pajak)
    print(hasil)
""",
    "deep": """\
# Contoh global variable dan deep nesting
g = 0

def analisis(data):
    global g
    for item in data:
        if item > 0:
            for sub in item:
                if sub != None:
                    if sub > 5:
                        if sub < 100:
                            g = g + sub
    print("selesai")
""",
    "all": """\
# Demo semua antipattern
g_counter = 0

def p(a, b, c, d, e, f, lst=[]):
    global g_counter
    g_counter += 1
    try:
        for item in a:
            if item:
                for sub in item:
                    if sub > 0:
                        if sub < 100:
                            if len(lst) < 50:
                                lst.append(sub * 365)
                                print("Added:", sub)
    except:
        pass
    for x in b:
        if x > 0:
            for y in c:
                if y < 0:
                    for z in d:
                        if z == 0:
                            print("zero")

def q(a, b, c, d, e, f, lst=[]):
    global g_counter
    g_counter += 1
    try:
        for item in a:
            if item:
                for sub in item:
                    if sub > 0:
                        if sub < 100:
                            if len(lst) < 50:
                                lst.append(sub * 365)
                                print("Added:", sub)
    except:
        pass
""",
}


# ============================================================
# Fallback konten per rule — ditampilkan jika Gemini tidak tersedia
# ============================================================
FALLBACK: dict[str, dict] = {
    "R01_bare_except": {
        "explanation": "<code>except:</code> tanpa tipe menangkap SEMUA error termasuk <code>KeyboardInterrupt</code> dan <code>SystemExit</code>, sehingga program tidak bisa dihentikan dengan Ctrl+C dan bug ikut tertelan.",
        "fixed_code": "# Tangkap tipe error yang spesifik, jangan except polos\nexcept ValueError as e:\n    print(f\"Error: {e}\")",
    },
    "R02_non_descriptive_name": {
        "explanation": "Nama variabel satu huruf tidak menjelaskan tujuannya. Nama yang baik membuat kode bisa dibaca seperti kalimat tanpa komentar tambahan.",
        "fixed_code": "# Beri nama yang menjelaskan isinya\ntotal_harga = harga * jumlah   # bukan: x = h * j",
    },
    "R03_missing_docstring": {
        "explanation": "Fungsi tanpa docstring sulit dipahami orang lain. Docstring satu baris di awal fungsi sudah cukup menjelaskan tujuannya.",
        "fixed_code": "def nama_fungsi(...):\n    \"\"\"Jelaskan tujuan fungsi dalam satu kalimat.\"\"\"\n    ...",
    },
    "R04_magic_number": {
        "explanation": "Angka literal tanpa nama membingungkan pembaca — tidak jelas apa maksud angka tersebut. Beri nama lewat konstanta agar maksudnya terbaca.",
        "fixed_code": "# Beri nama pada angka agar maksudnya jelas\nBATAS = <angka>          # ganti <angka> dengan nilai aslimu\nif nilai > BATAS:\n    ...",
    },
    "R05_deep_nesting": {
        "explanation": "Nesting yang terlalu dalam membuat alur sulit diikuti. Pakai <em>early return</em> untuk menangani kasus khusus lebih dulu, lalu lanjutkan logika utama tanpa menjorok dalam.",
        "fixed_code": "# Early return memangkas nesting\nif not syarat:\n    return\n# logika utama tetap di level dangkal\n...",
    },
    "R06_long_function": {
        "explanation": "Fungsi yang terlalu panjang sulit di-review dan diuji. Pecah menjadi beberapa fungsi kecil yang masing-masing melakukan satu tugas.",
        "fixed_code": "# Pecah jadi fungsi kecil bertugas tunggal\ndef fungsi_utama(data):\n    hasil = proses(data)\n    return hasil",
    },
    "R07_too_many_params": {
        "explanation": "Terlalu banyak parameter menyulitkan pemanggilan dan rawan salah urutan argumen. Kelompokkan parameter terkait ke dalam satu objek.",
        "fixed_code": "# Kelompokkan parameter ke satu objek\ndef fungsi(data):       # data memuat field yang diperlukan\n    ...",
    },
    "R08_mutable_default": {
        "explanation": "List/dict/set sebagai default argument dipakai bersama oleh SEMUA pemanggilan, sehingga nilai lama ikut terbawa — bug klasik Python. Gunakan <code>None</code> lalu buat objek baru di dalam fungsi.",
        "fixed_code": "# Pakai None, buat objek baru di dalam fungsi\ndef fungsi(data=None):\n    if data is None:\n        data = []",
    },
    "R09_print_debug": {
        "explanation": "<code>print()</code> di dalam fungsi biasanya sisa debugging. Gunakan modul <code>logging</code> yang bisa dimatikan tanpa mengubah kode.",
        "fixed_code": "# Ganti print debug dengan logging\nimport logging\nlogging.debug(f\"nilai: {data}\")",
    },
    "R10_no_return": {
        "explanation": "Fungsi yang menghitung sesuatu tapi tidak <code>return</code> memaksa pemanggil bergantung pada variabel global/efek samping. Kembalikan hasilnya.",
        "fixed_code": "# Kembalikan hasil lewat return\ndef hitung(...):\n    ...\n    return hasil",
    },
    "R11_hardcoded_string": {
        "explanation": "String yang sama muncul berulang. Bila perlu diganti, harus diubah di banyak tempat dan rawan terlewat. Simpan sekali sebagai konstanta.",
        "fixed_code": "# Simpan string berulang sebagai konstanta\nSTATUS_LULUS = \"lulus\"\nif status == STATUS_LULUS:\n    ...",
    },
    "R12_global_variable": {
        "explanation": "Variabel global membuat fungsi bergantung pada state di luar dirinya, menyulitkan testing dan pelacakan bug. Oper nilai lewat parameter dan kembalikan hasilnya.",
        "fixed_code": "# Hindari global: oper lewat parameter, kembalikan hasil\ndef tambah(total, nilai):\n    return total + nilai\ntotal = tambah(total, nilai)",
    },
    "R13_empty_except": {
        "explanation": "<code>except: pass</code> menelan error secara diam-diam sehingga bug tersembunyi tidak ketahuan. Minimal catat errornya sebelum melanjutkan.",
        "fixed_code": "# Jangan telan error; catat dulu\nexcept Exception as e:\n    logging.error(e)",
    },
    "R14_infinite_loop_risk": {
        "explanation": "<code>while True</code> tanpa jalan keluar yang jelas berisiko menggantung program selamanya. Pastikan ada kondisi berhenti atau <code>break</code>.",
        "fixed_code": "# Beri kondisi keluar yang jelas\nwhile not selesai:\n    ...\n    selesai = cek_kondisi()",
    },
    "R15_code_duplication": {
        "explanation": "Dua fungsi yang isinya hampir sama berarti perbaikan bug harus dilakukan di dua tempat dan satu sering terlewat. Satukan menjadi satu fungsi bersama.",
        "fixed_code": "# Satukan kode kembar jadi satu fungsi\ndef proses(...):\n    ...      # logika bersama dipakai keduanya",
    },
}


# ============================================================
# Jawaban UMUM & UNIVERSAL — dipakai bila rule tidak ada di FALLBACK
# (mis. rule baru ditambahkan) DAN LLM tidak terhubung.
# ============================================================
_DEFAULT_FIXED_CODE = (
    "# Terapkan prinsip clean code pada baris yang ditandai:\n"
    "# nama jelas · satu tugas per fungsi · tangani error · hindari pengulangan"
)


def _default_explanation(v: dict) -> str:
    """Penjelasan umum & universal untuk antipattern apa pun tanpa LLM."""
    return (
        f"Terdeteksi antipattern <code>{v['rule_name']}</code> pada baris {v['line_no']}. "
        "Pola seperti ini umumnya membuat kode lebih sulit dibaca, diuji, atau "
        "rawan menimbulkan bug tersembunyi. Tinjau kembali baris tersebut lalu "
        "sederhanakan mengikuti prinsip clean code (nama jelas, satu tugas per "
        "fungsi, tangani error secara eksplisit, dan hindari pengulangan)."
    )


# ============================================================
# Pydantic model untuk request body
# ============================================================
class AnalyzeRequest(BaseModel):
    code: str


# ============================================================
# API Endpoints — didefinisikan SEBELUM StaticFiles mount
# ============================================================

@app.get("/api/samples/{key}")
async def get_sample(key: str):
    """Kembalikan kode contoh berdasarkan key (basic/magic/deep/all)."""
    if key not in SAMPLES:
        raise HTTPException(status_code=404, detail=f"Sample '{key}' tidak ditemukan")
    return {"code": SAMPLES[key]}


SAMPLES_DIR = Path(__file__).parent / "samples"

@app.get("/api/files")
async def list_sample_files():
    """Kembalikan daftar file .py di folder samples/."""
    files = sorted(SAMPLES_DIR.glob("*.py"))
    return {"files": [f.name for f in files]}

@app.get("/api/files/{filename}")
async def get_sample_file(filename: str):
    """Kembalikan isi file sample berdasarkan nama file."""
    if not filename.endswith(".py") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nama file tidak valid")
    path = SAMPLES_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' tidak ditemukan")
    return {"filename": filename, "code": path.read_text(encoding="utf-8")}


@app.get("/api/rules")
async def get_rules():
    """Kembalikan metadata semua 15 rules dari Knowledge Base."""
    kb = KnowledgeBase()
    return {"rules": kb.describe(), "total": len(kb)}


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    """
    Endpoint utama: terima kode Python, jalankan inference engine + Gemini.

    Menggunakan def (bukan async def) agar time.sleep() di dalam
    generate_feedback() berjalan di thread pool dan tidak memblokir event loop.

    Returns:
        {
          "violations": [...],  // list violation dengan explanation & fixed_code
          "summary": {...}      // statistik by severity
        }
    """
    code = request.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="Kode tidak boleh kosong")

    # STEP 1: Jalankan forward chaining rule engine
    engine = InferenceEngine()
    try:
        violations = engine.run(code)
    except SyntaxError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Syntax error pada baris {e.lineno}: {e.msg}"
        )

    summary = engine.summary(violations)
    v_dicts = [v.to_dict() for v in violations]

    # STEP 2: Deduplikasi per rule_id sebelum kirim ke Gemini
    # Rule yang sama (mis. R01 muncul 3x) cukup 1 panggilan — penjelasannya sama
    unique_v_dicts = list({v["rule_id"]: v for v in v_dicts}.values())
    feedbacks = generate_feedback(unique_v_dicts)

    # Buat lookup: rule_id → hasil LLM
    # Catatan: jika rule_id muncul lebih dari sekali (mis. R03 untuk 2 fungsi),
    # penjelasan yang sama tetap relevan karena rule-nya sama.
    feedback_map = {
        f["rule_id"]: f["hasil_llm"]
        for f in feedbacks
        if f.get("hasil_llm")
    }

    # STEP 3: Gabungkan violations + LLM feedback ke format yang dipakai frontend
    result_violations = []
    for v in v_dicts:
        llm      = feedback_map.get(v["rule_id"]) or {}
        fallback = FALLBACK.get(v["rule_id"], {})
        # Sumber penjelasan: "ai" bila berasal dari LLM, selain itu "fallback".
        # Dipakai frontend untuk menampilkan badge AI vs umum per kartu.
        source = "ai" if llm.get("penjelasan") else "fallback"
        result_violations.append({
            "rule_id":     v["rule_id"],
            "rule_name":   v["rule_name"],
            "severity":    v["severity"],
            "line_no":     v["line_no"],
            "snippet":     v["snippet"],
            # Selalu ada jawaban: LLM -> fallback per-rule -> default universal
            "explanation": llm.get("penjelasan")     or fallback.get("explanation") or _default_explanation(v),
            "fixed_code":  llm.get("kode_perbaikan") or fallback.get("fixed_code")  or _DEFAULT_FIXED_CODE,
            "source":      source,
        })

    return {
        "violations": result_violations,
        "summary": summary,
        # Beri tahu frontend apakah penjelasan berasal dari LLM atau fallback umum
        "llm_used": bool(feedback_map),
    }


# ============================================================
# Static file serving — HARUS di bawah semua route API
# ============================================================
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
