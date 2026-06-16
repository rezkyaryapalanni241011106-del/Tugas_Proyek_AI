# AI Code Review Tutor

Sistem AI untuk mendeteksi antipattern pada kode Python mahasiswa pemrograman dasar, menggunakan **Rule-Based Reasoning (Forward Chaining)** sebagai inti deteksi dan **LLM (multi-provider: Groq / OpenAI / Gemini / Claude / DeepSeek)** sebagai penjelas umpan balik edukatif. Penyedia LLM dapat diganti hanya dengan mengubah `LLM_PROVIDER` di file `.env`.

> Proyek ini dikembangkan sebagai tugas mata kuliah Kecerdasan Buatan, Semester Genap 2025/2026  
> Institut Teknologi Bacharuddin Jusuf Habibie

---

## Daftar Isi

1. [Gambaran Sistem](#gambaran-sistem)
2. [Arsitektur](#arsitektur)
3. [Prasyarat](#prasyarat)
4. [Cara Instalasi](#cara-instalasi)
5. [Cara Menjalankan](#cara-menjalankan)
6. [Setup API Key & Pilih Penyedia LLM](#setup-api-key--pilih-penyedia-llm)
7. [15 Rules Antipattern](#15-rules-antipattern)
8. [Struktur Proyek](#struktur-proyek)
9. [Menjalankan Unit Test](#menjalankan-unit-test)
10. [Tim Pengembang](#tim-pengembang)

---

## Gambaran Sistem

Mahasiswa pemrograman dasar sering menulis kode yang *berjalan* tapi mengandung **antipattern** — kebiasaan menulis kode yang buruk seperti nama variabel tidak jelas, magic number, atau exception yang tidak ditangani. Masalah ini sulit dideteksi secara manual oleh dosen karena keterbatasan waktu.

**AI Code Review Tutor** menyelesaikan masalah ini melalui empat tahap:

```
Kode Python Mahasiswa
        │
        ▼
[1] AST Parser         ← modul ast bawaan Python
        │
        ▼
[2] Inference Engine   ← forward chaining terhadap 15 rules
        │
        ▼
[3] LLM Explainer      ← Groq/OpenAI/Gemini/Claude/DeepSeek (hanya penjelas, BUKAN detektor)
        │
        ▼
Panel Umpan Balik Edukatif
(penjelasan + kode perbaikan + soal latihan)
diurutkan: CRITICAL → HIGH → MEDIUM → LOW
```

**Prinsip utama:** LLM *tidak* menentukan ada/tidaknya pelanggaran. Seluruh deteksi dilakukan oleh rule engine yang deterministik, sehingga tidak ada risiko *hallucination* dalam proses deteksi.

---

## Arsitektur

State sistem direpresentasikan sebagai **S = (C, T, V, F)**:

| Komponen | Tipe | Deskripsi |
|---|---|---|
| C | `string` | Kode Python mahasiswa yang dianalisis |
| T | `ASTNode` | Abstract Syntax Tree hasil parsing kode C |
| V | `Set<Violation>` | Himpunan antipattern yang terdeteksi oleh rule engine |
| F | `Set<Feedback>` | Himpunan umpan balik edukatif yang dihasilkan LLM |

### Komponen Sistem

| Komponen | File | Teknologi |
|---|---|---|
| AST Parser | `core/parser.py` | `ast` (built-in Python) |
| Knowledge Base (15 rules) | `core/knowledge_base.py` | Python murni |
| Inference Engine | `core/inference_engine.py` | Forward chaining |
| Abstraksi Multi-Provider LLM | `core/llm_providers.py` | Groq / OpenAI / Gemini / Claude / DeepSeek |
| LLM Explainer | `core/llm_explainer.py` | Prompt + parsing (provider-agnostic) |
| Web Interface | `frontend/` | HTML / CSS / JavaScript |
| REST API Server | `app.py` | FastAPI + Uvicorn |
| CLI | `main.py` | Python standard library |

---

## Prasyarat

- **Python 3.8 atau lebih baru**
- **pip** (manajer paket Python)
- Koneksi internet (untuk fitur penjelasan LLM — opsional)
- API key salah satu penyedia LLM (Groq gratis & disarankan — opsional)

---

## Cara Instalasi

### 1. Download atau Clone Proyek

Letakkan folder proyek di lokasi yang diinginkan.

### 2. Buat Virtual Environment (Disarankan)

```bash
python -m venv venv
```

Aktifkan virtual environment:

- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependensi

```bash
pip install -r requirements.txt
```

### 4. Salin File Konfigurasi

Buat file `.env` di root folder proyek:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Kemudian pilih penyedia LLM dan isi API key-nya di file `.env` (lihat [Setup API Key & Pilih Penyedia LLM](#setup-api-key--pilih-penyedia-llm)).

---

## Cara Menjalankan

### A. Web Interface (Direkomendasikan)

**Windows** — Jalankan launcher otomatis:

```powershell
.\run.ps1
```

Launcher akan otomatis membuka browser ke `http://localhost:8080`.

Atau jalankan server secara manual:

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8080
```

Buka browser dan akses: **`http://localhost:8080`**

#### Cara Penggunaan Web Interface

1. Tempel kode Python yang ingin dianalisis di area editor
2. Klik tombol **"Analisis"** atau tekan **Ctrl + Enter**
3. Hasil akan ditampilkan berupa kartu violation, diurutkan dari tingkat keparahan tertinggi
4. Setiap kartu berisi: penjelasan antipattern, contoh kode perbaikan, dan soal latihan

### B. Command Line Interface (CLI)

Analisis file Python secara langsung dari terminal:

```bash
# Analisis file tertentu
python main.py path/ke/kode.py

# Analisis dengan output JSON (termasuk penjelasan LLM)
python main.py path/ke/kode.py --json

# Tampilkan log rule firings (untuk debugging/demo)
python main.py path/ke/kode.py --trace

# Tampilkan katalog semua 15 rules
python main.py --rules

# Analisis tanpa warna (untuk output ke file)
python main.py path/ke/kode.py --no-color
```

#### Contoh output CLI:

```
=== AI Code Review Tutor ===
Menganalisis: samples/sample_01_kalkulator.py
─────────────────────────────────────────────
[HIGH]     R01  baris 12  Bare except (except tanpa tipe Exception)
[MEDIUM]   R04  baris 23  Magic Number (angka tanpa nama/konteks)
[MEDIUM]   R12  baris 31  Penggunaan keyword `global`
─────────────────────────────────────────────
Total: 3 violations  (HIGH: 1, MEDIUM: 2)
```

---

## Setup API Key & Pilih Penyedia LLM

Sistem mendukung **5 penyedia LLM**. Pilih salah satu lewat `LLM_PROVIDER` di `.env`, lalu isi API key penyedia tersebut. Rule engine tetap berjalan **tanpa API key** — hasilnya berupa daftar violation dengan **penjelasan umum** (fallback) untuk setiap rule.

### Penyedia yang Didukung

| `LLM_PROVIDER` | Penyedia | Model default | Env API key | Catatan |
|---|---|---|---|---|
| `groq` | Groq | `llama-3.3-70b-versatile` | `GROQ_API_KEY` | **Gratis**, disarankan |
| `openai` | OpenAI (ChatGPT) | `gpt-4o-mini` | `OPENAI_API_KEY` | Berbayar |
| `gemini` | Google Gemini | `gemini-2.0-flash` | `GEMINI_API_KEY` | Ada tier gratis |
| `claude` | Anthropic (Claude) | `claude-3-5-haiku-latest` | `ANTHROPIC_API_KEY` | Berbayar |
| `deepseek` | DeepSeek | `deepseek-chat` | `DEEPSEEK_API_KEY` | Berbayar, murah |

> Model default tiap penyedia bisa ditimpa lewat `LLM_MODEL` di `.env`.

### Cara Mengaktifkan

1. Pasang SDK penyedia yang dipakai (sudah termasuk di `requirements.txt`):
   - Groq → `pip install groq`
   - OpenAI / DeepSeek → `pip install openai`
   - Gemini → `pip install google-genai`
   - Claude → `pip install anthropic`
2. Buka `.env`, pilih penyedia dan isi key-nya. Contoh memakai Groq:

   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_...kunci-anda-di-sini
   ```

   Ingin mencoba penyedia lain? Cukup ganti `LLM_PROVIDER` dan isi key-nya, lalu **restart server**:

   ```env
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=AIza...
   ```

3. Verifikasi penyedia aktif lewat endpoint diagnostik: `GET http://localhost:8080/api/llm`.

### Cara Mendapatkan API Key

- **Groq** (gratis): [console.groq.com](https://console.groq.com) → API Keys → Create API Key
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Gemini**: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **Claude**: [console.anthropic.com](https://console.anthropic.com/settings/keys)
- **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com/api_keys)

> **Catatan Keamanan:** Jangan pernah commit file `.env` ke repository publik.

---

## 15 Rules Antipattern

Sistem mendeteksi 15 antipattern yang dibagi dalam 5 topik pemrograman dasar:

### Variabel

| ID | Nama Rule | Kondisi IF | Severity |
|---|---|---|---|
| R02 | Non-Descriptive Name | Nama variabel/parameter 1 huruf di luar `{i,j,k,x,y,n,_}` | MEDIUM |
| R04 | Magic Number | Angka literal di luar `{0, 1, -1}`, bukan di dalam `range()` | MEDIUM |
| R11 | Hardcoded String | String literal sama muncul ≥2x dalam konteks Compare/Assign | MEDIUM |
| R12 | Global Variable | Penggunaan keyword `global` | MEDIUM |

### Fungsi

| ID | Nama Rule | Kondisi IF | Severity |
|---|---|---|---|
| R03 | Missing Docstring | FunctionDef tanpa docstring sebagai pernyataan pertama | LOW |
| R06 | Long Function | Fungsi dengan `len(body) > 20` statement | MEDIUM |
| R07 | Too Many Parameters | Fungsi dengan `len(args) > 5` parameter | MEDIUM |
| R08 | Mutable Default Argument | Default argument berupa `list`, `dict`, atau `set` literal | HIGH |
| R09 | Print Debug | `print()` dipanggil di dalam fungsi | LOW |
| R10 | Function Tanpa Return | Fungsi melakukan komputasi (Assign/For/While) tanpa `return` | HIGH |

### Loop

| ID | Nama Rule | Kondisi IF | Severity |
|---|---|---|---|
| R05 | Deep Nesting | Kedalaman nesting `> 4` tingkat | HIGH |
| R14 | Infinite Loop Risk | `while True` tanpa `break` di dalamnya | CRITICAL |

### Exception Handling

| ID | Nama Rule | Kondisi IF | Severity |
|---|---|---|---|
| R01 | Bare Except | `except:` tanpa tipe exception | HIGH |
| R13 | Empty Except | `except` clause yang hanya berisi `pass` | CRITICAL |

### Modularitas

| ID | Nama Rule | Kondisi IF | Severity |
|---|---|---|---|
| R15 | Code Duplication | Dua fungsi dengan similarity >80% dan body ≥4 baris | HIGH |

### Tingkat Keparahan

| Level | Arti |
|---|---|
| 🔴 CRITICAL | Harus diperbaiki segera — berpotensi menyebabkan bug tersembunyi |
| 🟠 HIGH | Sangat disarankan diperbaiki — merusak keterbacaan/keandalan |
| 🟡 MEDIUM | Disarankan diperbaiki — melanggar clean code principles |
| 🔵 LOW | Sebaiknya diperbaiki — praktik yang lebih baik tersedia |

---

## Struktur Proyek

```
ai-code-review-tutor/
│
├── app.py                      # Server FastAPI (REST API + static files)
├── main.py                     # CLI runner
├── requirements.txt            # Dependensi Python
├── .env                        # Konfigurasi API key (tidak di-commit)
├── .env.example                # Template konfigurasi
├── run.ps1                     # Launcher Windows (PowerShell)
├── run.bat                     # Launcher Windows (Batch)
│
├── core/                       # Backend — Rule Engine & LLM
│   ├── __init__.py
│   ├── models.py               # Severity enum, Violation dataclass
│   ├── parser.py               # AST parser dan utilitas traversal
│   ├── knowledge_base.py       # 15 rules antipattern (R01–R15)
│   ├── inference_engine.py     # Forward chaining inference engine
│   ├── llm_providers.py        # Abstraksi multi-provider LLM (Groq/OpenAI/Gemini/Claude/DeepSeek)
│   └── llm_explainer.py        # Prompt + parsing feedback (provider-agnostic)
│
├── frontend/                   # Web Interface
│   ├── index.html              # Single-page application
│   ├── script.js               # Logika interaktif & API calls
│   └── style.css               # Styling Material Design
│
├── tests/                      # Unit & Integrasi Test (pytest)
│   ├── __init__.py
│   ├── conftest.py             # Konfigurasi pytest (sys.path)
│   ├── test_rules.py           # Test case untuk R01–R15
│   ├── test_inference_engine.py# Test perilaku engine & KnowledgeBase
│   └── test_parser.py          # Test utilitas AST parser
│
└── samples/                    # Kode mahasiswa untuk demo & pengujian
    ├── sample_bad_code.py          # Demo CLI (sudah ada)
    ├── sample_01_kalkulator.py     # R01, R03, R04, R09, R12
    ├── sample_02_pengecekan_nilai.py   # R03, R04, R10, R12, R13
    ├── sample_03_manajemen_siswa.py    # R03, R06, R07, R09, R10
    ├── sample_04_inventori_toko.py     # R03, R04, R08, R15
    ├── sample_05_matematika_dasar.py   # R02, R03, R04, R09, R10
    ├── sample_06_sistem_login.py       # R03, R11, R13, R14
    ├── sample_07_rekening_bank.py      # R01, R03, R04, R05, R12
    ├── sample_08_konverter_satuan.py   # R02, R03, R04
    ├── sample_09_daftar_tugas.py       # R03, R09, R12, R13, R14
    ├── sample_10_perpustakaan.py       # R01, R03, R07, R08, R10
    ├── sample_11_kuis_matematika.py    # R03, R04, R09, R15
    └── sample_12_analisis_nilai.py     # R02, R03, R05, R11, R12
```

---

## Menjalankan Unit Test

Pastikan dependensi sudah terinstal (termasuk `pytest`):

```bash
pip install -r requirements.txt
```

### Jalankan Semua Test

```bash
pytest tests/ -v
```

### Jalankan Test per Kategori

```bash
# Hanya test rules (R01–R15)
pytest tests/test_rules.py -v

# Hanya test inference engine
pytest tests/test_inference_engine.py -v

# Hanya test parser
pytest tests/test_parser.py -v
```

### Jalankan Test Spesifik

```bash
# Satu rule saja
pytest tests/test_rules.py::TestR01BareExcept -v

# Satu metode test saja
pytest tests/test_rules.py::TestR01BareExcept::test_positive_bare_except_dengan_print -v
```

#### Contoh Output Test Berhasil

```
tests/test_rules.py::TestR01BareExcept::test_positive_bare_except_dengan_print PASSED
tests/test_rules.py::TestR01BareExcept::test_negative_except_dengan_tipe_spesifik PASSED
...
tests/test_inference_engine.py::TestKnowledgeBase::test_kb_memiliki_tepat_15_rules PASSED
─────────────────────────────────────────────────────────────
123 passed in 0.16s
```

Pengujian mengikuti **Proposal Section 8.3 Lapisan 1**: setiap rule (R01–R15) diuji dengan kasus *positive* (kode yang sengaja mengandung antipattern → harus terdeteksi) dan kasus *negative* (kode bersih → tidak boleh memicu violation), untuk menjamin target *Precision* 100%.

---

## Tim Pengembang

**Kelompok Coders — Kelas IK24ABC**  
Institut Teknologi Bacharuddin Jusuf Habibie

| NIM | Nama | Komponen |
|---|---|---|
| 241011106 | Rezky Arya Palanni *(Ketua)* | AST Parser + Knowledge Base (15 rules) |
| 241011128 | Andi Ahmad Naufal Madani | Inference Engine (forward chaining) |
| 241011110 | Habel Mangopo | LLM Integration (multi-provider: Groq/OpenAI/Gemini/Claude/DeepSeek) |
| 241011123 | Muhammad Arkan Naim | User Interface (HTML/CSS/JS) |
| 241011124 | Muhammad Akmal Ahsan | Testing, Evaluasi, dan Dokumentasi |

---

## Referensi

- Gulabovska, H., & Porkoláb, Z. (2019). Survey on static analysis tools of Python programs. *CEUR Workshop Proceedings, 2508.* https://ceur-ws.org/Vol-2508/paper-gul.pdf

- Khati, D., Rodriguez-Cardenas, D., Pantzer, P., & Poshyvanyk, D. (2026). Detecting and correcting hallucinations in LLM-generated code via deterministic AST analysis. *arXiv preprint arXiv:2601.19106.* https://arxiv.org/abs/2601.19106

- Lee, Y., Song, J. Y., Kim, D., Kim, J., Kim, M., & Nam, J. (2025). Hallucination by code generation LLMs: Taxonomy, benchmarks, mitigation, and challenges. *arXiv preprint arXiv:2504.20799.* https://arxiv.org/abs/2504.20799

- Liu, F., Liu, Y., Shi, L., Huang, H., Wang, R., Yang, Z., & Zhang, L. (2024). Exploring and evaluating hallucinations in LLM-powered code generation. *arXiv preprint arXiv:2404.00971.* https://arxiv.org/abs/2404.00971

- Pankiewicz, M., & Baker, R. S. (2023). Large language models (GPT) for automating feedback on programming assignments. *Proceedings of the 31st International Conference on Computers in Education (ICCE).* Asia-Pacific Society for Computers in Education.

- Phung, T., Cambronero, J., Gulwani, S., Kohn, T., Majumdar, R., Singla, A., & Soares, G. (2023). Generating high-precision feedback for programming syntax errors using large language models. *arXiv preprint arXiv:2302.04662.* https://arxiv.org/abs/2302.04662

- Pitts, G., Hridi, A. P., & Lekshmi-Narayanan, A.-B. (2025). A survey of LLM-based applications in programming education: Balancing automation and human oversight. *arXiv preprint arXiv:2510.03719.* https://arxiv.org/abs/2510.03719

- Russell, S., & Norvig, P. (2010). *Artificial intelligence: A modern approach* (3rd ed.). Prentice Hall.

- Zhang, Z., Dong, Z., Shi, Y., Price, T., Matsuda, N., & Xu, D. (2024). Students' perceptions and preferences of generative artificial intelligence feedback for programming. *Proceedings of the AAAI Conference on Artificial Intelligence, 38*(21), 23250–23258. https://doi.org/10.1609/aaai.v38i21.30372
