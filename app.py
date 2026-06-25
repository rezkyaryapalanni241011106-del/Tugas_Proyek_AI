"""
app.py — FastAPI Server untuk AI Code Review Tutor.

Menggabungkan static file serving + REST API:
  GET  /api/samples/{key}  → Kembalikan kode contoh (basic/magic/deep/all)
  POST /api/analyze        → Jalankan rule engine + LLM, kembalikan violations
  GET  /api/rules          → Metadata semua 15 rules
  GET  /api/llm            → Info penyedia LLM aktif (provider, model, status)
  GET  /                   → Sajikan index.html (frontend)

Cara menjalankan (pilih salah satu):
  1. Klik dua kali run.bat            ← termudah, otomatis install & buka browser
  2. .\run.ps1                         ← dari PowerShell
  3. Manual:
       pip install -r requirements.txt
       python app.py                   ← atau: uvicorn app:app --port 8080

  Catatan: JANGAN pakai --reload. --reload membuat server RESTART setiap ada
  file yang berubah, sehingga sesi bisa terputus di tengah jalan.

Buka browser: http://localhost:8080

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.inference_engine import InferenceEngine
from core.knowledge_base import KnowledgeBase
from core.llm_explainer import generate_feedback
from core.llm_providers import resolve_provider

# Paksa UTF-8 di terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

app = FastAPI(title="AI Code Review Tutor", version="1.0.0", docs_url="/docs")


@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    """Cegah browser meng-cache aset frontend (js/css/html).

    Tanpa ini, browser sering menyajikan script.js versi lama dari cache
    sehingga perubahan kode tidak terlihat walau sudah refresh biasa.
    """
    response = await call_next(request)
    path = request.url.path
    if path.endswith((".js", ".css", ".html")) or path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

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
# Fallback konten per rule — ditampilkan jika LLM tidak tersedia
# (API key kosong, rate limit, atau error penyedia)
# ============================================================
FALLBACK: dict[str, dict] = {
    "R01_bare_except": {
        "explanation": "<code>except:</code> tanpa tipe error menangkap semua exception — termasuk <code>KeyboardInterrupt</code> yang mencegah program dihentikan dengan Ctrl+C.",
        "fixed_code": "except ValueError:\n    ...",
    },
    "R02_non_descriptive_name": {
        "explanation": "Nama variabel satu huruf tidak mendeskripsikan isi atau tujuannya.",
        "fixed_code": "total_nilai = nilai1 + nilai2",
    },
    "R03_missing_docstring": {
        "explanation": "Fungsi ini memiliki &ge;5 statement tetapi tidak memiliki docstring (string keterangan tujuan) di baris pertama.",
        "fixed_code": "def nama_fungsi(...):\n    \"\"\"Jelaskan tujuan fungsi.\"\"\"\n    ...",
    },
    "R04_magic_number": {
        "explanation": "Angka literal tanpa nama tidak jelas maknanya dalam kode — definisikan sebagai konstanta bernama.",
        "fixed_code": "NILAI_MAKSIMAL = 100",
    },
    "R05_deep_nesting": {
        "explanation": "Nesting lebih dari 4 tingkat membuat alur kode sulit dibaca dan di-debug.",
        "fixed_code": "if not syarat:\n    return\n...",
    },
    "R06_long_function": {
        "explanation": "Fungsi dengan lebih dari 20 statement sebaiknya dipecah menjadi beberapa fungsi yang lebih kecil.",
        "fixed_code": "def proses_utama():\n    return langkah_kecil(...)",
    },
    "R07_too_many_params": {
        "explanation": "Fungsi dengan lebih dari 5 parameter rawan salah urutan argumen saat dipanggil.",
        "fixed_code": "def fungsi(data):  # data berisi semua field\n    ...",
    },
    "R08_mutable_default": {
        "explanation": "Default argument bertipe list/dict/set dipakai bersama semua pemanggilan fungsi — ini menyebabkan nilai lama ikut terbawa.",
        "fixed_code": "def fungsi(data=None):\n    if data is None:\n        data = []",
    },
    "R09_print_debug": {
        "explanation": "<code>print()</code> di dalam fungsi yang me-return nilai kemungkinan adalah sisa proses debugging.",
        "fixed_code": "logging.debug(f\"nilai: {data}\")",
    },
    "R10_no_return": {
        "explanation": "Fungsi ini menghitung hasil ke variabel lokal tetapi tidak mengembalikannya dengan <code>return</code>.",
        "fixed_code": "def hitung(...):\n    hasil = ...\n    return hasil",
    },
    "R11_hardcoded_string": {
        "explanation": "String yang sama muncul lebih dari sekali — simpan sebagai konstanta agar tidak perlu diganti di banyak tempat.",
        "fixed_code": "STATUS = \"lulus\"\nif nilai == STATUS:\n    ...",
    },
    "R12_global_variable": {
        "explanation": "Kata kunci <code>global</code> membuat fungsi bergantung pada state di luar scope-nya sendiri.",
        "fixed_code": "def tambah(total, nilai):\n    return total + nilai",
    },
    "R13_empty_except": {
        "explanation": "<code>except: pass</code> menelan error secara diam-diam — bug bisa tersembunyi tanpa diketahui.",
        "fixed_code": "except Exception as e:\n    logging.error(e)",
    },
    "R14_infinite_loop_risk": {
        "explanation": "<code>while True</code> tanpa <code>break</code>, <code>return</code>, atau <code>raise</code> yang jelas berisiko menggantung program.",
        "fixed_code": "while True:\n    if kondisi:\n        break",
    },
    "R15_code_duplication": {
        "explanation": "Dua fungsi ini memiliki isi yang sangat mirip (>80% sama) — satukan menjadi satu fungsi bersama.",
        "fixed_code": "def proses(...):\n    ...  # satu fungsi untuk keduanya",
    },
}


# ============================================================
# Jawaban UMUM & UNIVERSAL — dipakai bila rule tidak ada di FALLBACK
# (mis. rule baru ditambahkan) DAN LLM tidak terhubung.
# ============================================================
_DEFAULT_FIXED_CODE = "# Tinjau baris yang ditandai dan sesuaikan dengan prinsip clean code."


def _default_explanation(v: dict) -> str:
    """Penjelasan singkat untuk antipattern yang tidak ada entri FALLBACK-nya."""
    return (
        f"Terdeteksi <strong>{v['rule_name']}</strong> pada baris {v['line_no']}."
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


@app.get("/api/llm")
async def get_llm_info():
    """Info penyedia LLM aktif — untuk verifikasi konfigurasi .env.

    status: "ok" (siap dipakai) | "no_key" (key kosong) |
            "unknown_provider" (LLM_PROVIDER salah ketik).
    """
    provider, status, label = resolve_provider()
    return {
        "provider": label,
        "model": provider.model if provider else None,
        "status": status,
        "ready": provider is not None,
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    """
    Endpoint utama: terima kode Python, jalankan inference engine + LLM.

    Menggunakan def (bukan async def) agar pemanggilan LLM yang bersifat
    blocking berjalan di thread pool dan tidak memblokir event loop FastAPI.

    Returns:
        {
          "violations": [...],   // list violation dengan explanation & fixed_code
          "summary": {...},      // statistik by severity
          "llm_status": "...",   // ok | rate_limited | no_key | error
          "llm_used": bool,      // True jika penjelasan berasal dari LLM
          "llm_provider": "..."  // nama penyedia aktif (mis. "Groq")
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

    # STEP 2: Deduplikasi per rule_id sebelum kirim ke Groq
    # Rule yang sama (mis. R01 muncul 3x) cukup 1 panggilan — penjelasannya sama.
    # Urutkan CRITICAL→HIGH→MEDIUM→LOW agar bila ada cap di LLM explainer,
    # yang diprioritaskan selalu violations paling parah.
    _SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    unique_v_dicts = sorted(
        {v["rule_id"]: v for v in v_dicts}.values(),
        key=lambda v: _SEV_ORDER.get(v.get("severity", "LOW"), 99),
    )
    feedbacks, llm_status, llm_provider = generate_feedback(unique_v_dicts, source_code=code)

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
        # "ok" | "rate_limited" | "no_key" | "error"
        "llm_status": llm_status,
        "llm_used": bool(feedback_map),
        "llm_provider": llm_provider,
    }


# ============================================================
# Static file serving — HARUS di bawah semua route API
# ============================================================
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    # Port 8080 konsisten dengan run.bat / run.ps1.
    # Tanpa --reload agar sesi tidak terputus saat file berubah.
    uvicorn.run(app, host="127.0.0.1", port=8080)
