"""
test_rules.py — Unit test untuk 15 rules antipattern (R01–R15).

Sesuai Proposal Section 8.3 Lapisan 1:
  - Setiap rule diuji dengan 2-3 kode yang SENGAJA mengandung antipattern (True Positive)
  - Setiap rule diuji dengan 2   kode yang BERSIH dan tidak melanggar rule (True Negative)

Target metrik (Proposal Section 8.3):
  - Precision 100%  → tidak boleh ada False Positive
  - Recall tinggi   → semua antipattern nyata harus terdeteksi

Author  : Kelompok AI Code Review Tutor (Testing & Evaluasi)
NIM     : 241011124 — Muhammad Akmal Ahsan
Course  : Kecerdasan Buatan, Semester Genap 2025/2026
"""

import pytest
from core.inference_engine import InferenceEngine
from core.models import Severity

# ── singleton engine (dibuat sekali, dipakai semua test) ──────────────────
_engine = InferenceEngine()


def _violations(source: str, rule_id: str) -> list:
    """Jalankan engine, kembalikan hanya violations yang cocok dengan rule_id."""
    try:
        return [v for v in _engine.run(source) if v.rule_id == rule_id]
    except SyntaxError:
        return []


# ═══════════════════════════════════════════════════════════════════════════
# R01 — Bare Except
# ═══════════════════════════════════════════════════════════════════════════
class TestR01BareExcept:
    """R01: except clause tanpa tipe exception → severity HIGH."""
    RID = "R01_bare_except"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_bare_except_dengan_print(self):
        """except: tanpa tipe → harus terdeteksi."""
        code = """
try:
    hasil = 10 / 0
except:
    print("terjadi error")
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_bare_except_di_dalam_fungsi(self):
        """except: di dalam fungsi → harus terdeteksi."""
        code = """
def baca_file(nama_file):
    try:
        with open(nama_file) as f:
            return f.read()
    except:
        return ""
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_bare_except_di_antara_handler_spesifik(self):
        """except: campuran dengan handler spesifik → bare except harus terdeteksi."""
        code = """
try:
    nilai = int(input("Masukkan angka: "))
except ValueError:
    nilai = 0
except:
    print("error tidak diketahui")
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_except_dengan_tipe_spesifik(self):
        """except ZeroDivisionError: → tidak boleh terdeteksi sebagai R01."""
        code = """
try:
    x = 10 / 0
except ZeroDivisionError:
    x = 0
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_except_dengan_banyak_tipe(self):
        """except (ValueError, TypeError): → tidak boleh terdeteksi."""
        code = """
try:
    nilai = int("abc")
except (ValueError, TypeError):
    nilai = 0
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R02 — Non-Descriptive Name
# ═══════════════════════════════════════════════════════════════════════════
class TestR02NonDescriptiveName:
    """R02: nama variabel/parameter 1 huruf di luar {i,j,k,x,y,n,_} → severity MEDIUM."""
    RID = "R02_non_descriptive_name"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_variabel_satu_huruf(self):
        """Variabel 'a' → bukan dari daftar huruf yang diizinkan."""
        code = "a = 100"
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_parameter_satu_huruf(self):
        """Parameter 'b' dan 'c' di definisi fungsi → harus terdeteksi."""
        code = """
def hitung(b, c):
    return b + c
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_variabel_dalam_loop(self):
        """Variabel 'm' di dalam assignment → harus terdeteksi."""
        code = """
m = 10
t = m * 2
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_huruf_yang_diizinkan(self):
        """i, j, k, x, y, n adalah huruf yang diizinkan → tidak boleh terdeteksi."""
        code = """
for i in range(10):
    x = i * 2
    y = x + 1
    n = len([])
    j = n + k if True else 0
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_nama_deskriptif(self):
        """Nama variabel yang panjang dan jelas → tidak boleh terdeteksi."""
        code = """
total = 0
counter = 0
nama_siswa = "Budi"
nilai_akhir = 95
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R03 — Missing Docstring
# ═══════════════════════════════════════════════════════════════════════════
class TestR03MissingDocstring:
    """R03: fungsi tanpa docstring sebagai pernyataan pertama → severity LOW."""
    RID = "R03_missing_docstring"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_fungsi_hanya_return(self):
        """Fungsi dengan ≥5 statement tanpa docstring → harus terdeteksi."""
        code = """
def hitung_luas(panjang, lebar):
    p = panjang
    l = lebar
    luas = p * l
    keliling = 2 * (p + l)
    return luas
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_fungsi_dengan_komentar_bukan_docstring(self):
        """Komentar # bukan docstring; fungsi ≥5 statement harus tetap terdeteksi."""
        code = """
def cek_prima(n):
    # cek apakah n adalah bilangan prima
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, n):
        if n % i == 0:
            return False
    return True
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_beberapa_fungsi_tanpa_docstring(self):
        """Dua fungsi panjang (≥5 statement) tanpa docstring → keduanya harus terdeteksi."""
        code = """
def hitung_total(harga, jumlah, diskon, pajak, ongkir):
    subtotal = harga * jumlah
    potongan = subtotal * diskon
    kena_pajak = (subtotal - potongan) * pajak
    total = subtotal - potongan + kena_pajak + ongkir
    return total

def hitung_rata(nilai1, nilai2, nilai3, nilai4, nilai5):
    total = nilai1 + nilai2 + nilai3 + nilai4 + nilai5
    jumlah = 5
    rata = total / jumlah
    selisih = max(nilai1, nilai2, nilai3) - rata
    return rata
"""
        assert len(_violations(code, self.RID)) >= 2

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_fungsi_dengan_docstring_triple_quote(self):
        """Docstring triple-quote di baris pertama → tidak boleh terdeteksi."""
        code = '''
def hitung_luas(panjang, lebar):
    """Menghitung luas persegi panjang."""
    return panjang * lebar
'''
        assert len(_violations(code, self.RID)) == 0

    def test_negative_fungsi_dengan_docstring_single_quote(self):
        """Docstring single-quote juga valid → tidak boleh terdeteksi."""
        code = """
def sapa(nama):
    'Menampilkan salam kepada nama yang diberikan.'
    print(f"Halo, {nama}!")
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R04 — Magic Number
# ═══════════════════════════════════════════════════════════════════════════
class TestR04MagicNumber:
    """R04: angka literal di luar {0, 1, -1} tanpa nama konstanta → severity MEDIUM."""
    RID = "R04_magic_number"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_integer_dalam_assignment(self):
        """Angka 18 dalam assignment → harus terdeteksi."""
        code = "batas_usia = 18"
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_angka_dalam_perbandingan(self):
        """Angka 75 dalam perbandingan if → harus terdeteksi."""
        code = """
if nilai > 75:
    print("Lulus")
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_float_sebagai_pengali(self):
        """Float 0.11 sebagai multiplier → harus terdeteksi."""
        code = "ppn = harga * 0.11"
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_angka_yang_diizinkan(self):
        """0, 1, dan -1 adalah angka yang diizinkan → tidak boleh terdeteksi."""
        code = """
skor = 0
aktif = 1
mundur = -1
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_angka_di_dalam_range(self):
        """Angka di dalam range() dikecualikan → tidak boleh terdeteksi."""
        code = """
for i in range(10):
    print(i)
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R05 — Deep Nesting
# ═══════════════════════════════════════════════════════════════════════════
class TestR05DeepNesting:
    """R05: nesting lebih dari 4 tingkat → severity HIGH."""
    RID = "R05_deep_nesting"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_lima_tingkat_if_bersarang(self):
        """5 tingkat nesting (FunctionDef + 4 If) → harus terdeteksi."""
        code = """
def proses(data):
    if data:
        if len(data) > 0:
            for item in data:
                if item > 0:
                    if item < 100:
                        print(item)
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_campuran_struktur_kontrol(self):
        """Campuran If/For/While dengan 5 tingkat → harus terdeteksi."""
        code = """
def analisis(daftar):
    if daftar:
        for item in daftar:
            if item:
                while len(item) > 0:
                    if item[0] > 0:
                        item.pop(0)
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_tepat_empat_tingkat(self):
        """Tepat 4 tingkat nesting → tidak boleh terdeteksi (batas adalah > 4)."""
        code = """
def proses(data):
    if data:
        for item in data:
            if item > 0:
                print(item)
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_nesting_dangkal(self):
        """Nesting hanya 2 tingkat → tidak boleh terdeteksi."""
        code = """
def hitung(a, b):
    if a > 0:
        return a + b
    return b
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R06 — Long Function
# ═══════════════════════════════════════════════════════════════════════════
class TestR06LongFunction:
    """R06: fungsi dengan lebih dari 20 statement di body → severity MEDIUM."""
    RID = "R06_long_function"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_fungsi_21_statement(self):
        """21 statement di body fungsi → harus terdeteksi."""
        body = "\n".join(f"    x{i} = {i}" for i in range(21))
        code = f"def fungsi_panjang():\n{body}\n    return 0\n"
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_fungsi_banyak_print(self):
        """22 baris print dalam satu fungsi → harus terdeteksi."""
        body = "\n".join(f"    print('baris {i}')" for i in range(22))
        code = f"def tampilkan_semua():\n{body}\n"
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_tepat_20_statement(self):
        """Tepat 20 statement (batas adalah > 20) → tidak boleh terdeteksi."""
        body = "\n".join(f"    x{i} = {i}" for i in range(19))
        code = f"def fungsi_normal():\n{body}\n    return 0\n"
        assert len(_violations(code, self.RID)) == 0

    def test_negative_fungsi_pendek(self):
        """Fungsi dengan 3 statement → tidak boleh terdeteksi."""
        code = '''
def tambah(a, b):
    """Menjumlahkan dua angka."""
    hasil = a + b
    return hasil
'''
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R07 — Too Many Parameters
# ═══════════════════════════════════════════════════════════════════════════
class TestR07TooManyParams:
    """R07: fungsi dengan lebih dari 5 parameter → severity MEDIUM."""
    RID = "R07_too_many_params"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_enam_parameter(self):
        """6 parameter → harus terdeteksi."""
        code = """
def buat_profil(nama, usia, kota, pekerjaan, email, telepon):
    pass
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_delapan_parameter(self):
        """8 parameter → harus terdeteksi."""
        code = """
def hitung_nilai(uts, uas, tugas1, tugas2, tugas3, kuis1, kuis2, hadir):
    return (uts + uas) / 2
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_tepat_lima_parameter(self):
        """Tepat 5 parameter (batas adalah > 5) → tidak boleh terdeteksi."""
        code = """
def buat_siswa(nama, nis, kelas, jurusan, nilai):
    return {"nama": nama, "nis": nis}
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_tiga_parameter(self):
        """3 parameter → tidak boleh terdeteksi."""
        code = '''
def hitung_volume(panjang, lebar, tinggi):
    """Hitung volume balok."""
    return panjang * lebar * tinggi
'''
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R08 — Mutable Default Argument
# ═══════════════════════════════════════════════════════════════════════════
class TestR08MutableDefault:
    """R08: default argument berupa list/dict/set literal → severity HIGH."""
    RID = "R08_mutable_default"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_list_sebagai_default(self):
        """Default argument [] (list) → harus terdeteksi."""
        code = """
def tambah_item(item, keranjang=[]):
    keranjang.append(item)
    return keranjang
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_dict_sebagai_default(self):
        """Default argument {} (dict) → harus terdeteksi."""
        code = """
def update_data(kunci, nilai, data={}):
    data[kunci] = nilai
    return data
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_set_literal_sebagai_default(self):
        """Default argument {1, 2} (set literal) → harus terdeteksi."""
        code = """
def tambah_tag(tag, tags={"umum", "baru"}):
    tags.add(tag)
    return tags
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_none_sebagai_default(self):
        """None sebagai default (pola idiomatis yang benar) → tidak boleh terdeteksi."""
        code = """
def tambah_item(item, keranjang=None):
    if keranjang is None:
        keranjang = []
    keranjang.append(item)
    return keranjang
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_default_immutable(self):
        """String dan integer sebagai default (immutable) → tidak boleh terdeteksi."""
        code = """
def sapa(nama="Anonim", umur=0, aktif=True):
    print(f"{nama}, {umur} tahun")
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R09 — Print Debug
# ═══════════════════════════════════════════════════════════════════════════
class TestR09PrintDebug:
    """R09: pemanggilan print() di dalam fungsi → severity LOW."""
    RID = "R09_print_debug"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_print_di_dalam_fungsi(self):
        """print() di dalam fungsi yang memiliki return → harus terdeteksi."""
        code = """
def hitung(a, b):
    print(f"Menghitung {a} + {b}")
    return a + b
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_beberapa_print_dalam_fungsi(self):
        """Beberapa print() di dalam fungsi → semua harus terdeteksi."""
        code = """
def proses_data(data):
    print("Memulai proses...")
    hasil = [item * 2 for item in data]
    print(f"Selesai: {len(hasil)} item")
    return hasil
"""
        assert len(_violations(code, self.RID)) >= 2

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_print_di_level_modul(self):
        """print() di luar fungsi (level modul) → tidak boleh terdeteksi."""
        code = """
print("Program dimulai")
total = 100
print(f"Total: {total}")
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_fungsi_tanpa_print(self):
        """Fungsi yang tidak mengandung print() → tidak boleh terdeteksi."""
        code = '''
def hitung_rata(data):
    """Hitung nilai rata-rata."""
    return sum(data) / len(data)
'''
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R10 — No Return
# ═══════════════════════════════════════════════════════════════════════════
class TestR10NoReturn:
    """R10: fungsi melakukan komputasi (Assign/AugAssign/For/While) tanpa return → HIGH."""
    RID = "R10_no_return"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_assignment_tanpa_return(self):
        """Fungsi dengan Assign dan loop tapi tanpa return → harus terdeteksi."""
        code = """
def hitung_total(data):
    total = 0
    for item in data:
        total += item
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_augassign_tanpa_return(self):
        """Fungsi dengan AugAssign tanpa return → harus terdeteksi."""
        code = """
def akumulasi(nilai):
    total = 0
    total += nilai
    total *= 2
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_fungsi_dengan_return(self):
        """Fungsi yang menghitung dan mengembalikan nilai → tidak boleh terdeteksi."""
        code = """
def hitung_total(data):
    total = 0
    for item in data:
        total += item
    return total
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_fungsi_hanya_print(self):
        """Fungsi hanya berisi print() (tanpa Assign/For/While) → tidak terdeteksi."""
        code = """
def tampilkan_salam(nama):
    print(f"Halo, {nama}!")
    print("Selamat datang!")
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R11 — Hardcoded String
# ═══════════════════════════════════════════════════════════════════════════
class TestR11HardcodedString:
    """R11: string literal yang sama muncul ≥2 kali dalam konteks Compare/Assign → MEDIUM."""
    RID = "R11_hardcoded_string"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_string_berulang_dalam_compare(self):
        """String "admin" muncul dua kali dalam konteks Compare → harus terdeteksi."""
        code = """
def cek_akses(peran):
    if peran == "admin":
        return True
    if peran == "admin":
        return False
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_string_berulang_dalam_assign(self):
        """String "aktif" muncul dua kali dalam konteks Assign → harus terdeteksi."""
        code = """
status = "aktif"
status_default = "aktif"
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_string_hanya_sekali(self):
        """String yang hanya muncul sekali → tidak boleh terdeteksi."""
        code = """
if role == "superadmin":
    print("Akses diberikan")
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_string_dalam_print_bukan_compare_assign(self):
        """String dalam print() (bukan Compare/Assign) → tidak boleh terdeteksi."""
        code = """
print("halo dunia")
print("halo dunia")
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R12 — Global Variable
# ═══════════════════════════════════════════════════════════════════════════
class TestR12GlobalVariable:
    """R12: penggunaan keyword `global` → severity MEDIUM."""
    RID = "R12_global_variable"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_global_dalam_fungsi(self):
        """global counter di dalam fungsi → harus terdeteksi."""
        code = """
counter = 0

def tambah_counter():
    global counter
    counter += 1
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_beberapa_global(self):
        """Dua global statement → keduanya harus terdeteksi."""
        code = """
skor = 0
nyawa = 3

def reset_game():
    global skor
    global nyawa
    skor = 0
    nyawa = 3
"""
        assert len(_violations(code, self.RID)) >= 2

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_tanpa_keyword_global(self):
        """Fungsi tanpa keyword global → tidak boleh terdeteksi."""
        code = """
def hitung(a, b):
    hasil = a + b
    return hasil
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_assignment_di_modul(self):
        """Assignment biasa di level modul (bukan keyword global) → tidak terdeteksi."""
        code = """
total = 0
total += 10
nama = "Program"
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R13 — Empty Except
# ═══════════════════════════════════════════════════════════════════════════
class TestR13EmptyExcept:
    """R13: except clause yang hanya berisi `pass` → severity CRITICAL."""
    RID = "R13_empty_except"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_except_bertipe_dengan_pass(self):
        """except ValueError: pass → harus terdeteksi (menyembunyikan error)."""
        code = """
try:
    hasil = 10 / 0
except ZeroDivisionError:
    pass
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_bare_except_dengan_pass(self):
        """except: pass (bare + empty) → harus terdeteksi."""
        code = """
try:
    f = open("data.txt")
except:
    pass
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_except_dengan_penanganan(self):
        """except ValueError: print(...) → tidak boleh terdeteksi sebagai R13."""
        code = """
try:
    nilai = int("bukan angka")
except ValueError:
    print("Input tidak valid")
    nilai = 0
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_except_dengan_beberapa_statement(self):
        """except dengan lebih dari satu statement → tidak boleh terdeteksi."""
        code = """
try:
    data = open("file.txt").read()
except IOError:
    data = ""
    print("File tidak ditemukan, menggunakan nilai kosong")
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R14 — Infinite Loop Risk
# ═══════════════════════════════════════════════════════════════════════════
class TestR14InfiniteLoopRisk:
    """R14: while True tanpa break → severity CRITICAL."""
    RID = "R14_infinite_loop_risk"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_while_true_tanpa_break(self):
        """while True tanpa break → harus terdeteksi."""
        code = """
counter = 0
while True:
    counter += 1
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_while_true_dengan_continue_saja(self):
        """while True dengan hanya continue (tanpa break) → harus terdeteksi."""
        code = """
i = 0
while True:
    i += 1
    if i < 10:
        continue
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_while_true_dengan_break(self):
        """while True dengan break → tidak boleh terdeteksi (aman)."""
        code = """
while True:
    perintah = input("Masukkan perintah (quit untuk keluar): ")
    if perintah == "quit":
        break
    print(f"Perintah: {perintah}")
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_while_dengan_kondisi_biasa(self):
        """while dengan kondisi variabel (bukan True literal) → tidak terdeteksi."""
        code = """
i = 0
while i < 10:
    print(i)
    i += 1
"""
        assert len(_violations(code, self.RID)) == 0


# ═══════════════════════════════════════════════════════════════════════════
# R15 — Code Duplication
# ═══════════════════════════════════════════════════════════════════════════
class TestR15CodeDuplication:
    """R15: dua fungsi dengan similarity >80% dan body ≥4 baris → severity HIGH."""
    RID = "R15_code_duplication"

    # ── True Positive ──────────────────────────────────────────────────────

    def test_positive_dua_fungsi_identik(self):
        """Dua fungsi yang isinya persis sama → harus terdeteksi."""
        code = """
def hitung_rata_kelas_a(data):
    total = 0
    jumlah = 0
    for nilai in data:
        total += nilai
        jumlah += 1
    return total / jumlah


def hitung_rata_kelas_b(data):
    total = 0
    jumlah = 0
    for nilai in data:
        total += nilai
        jumlah += 1
    return total / jumlah
"""
        assert len(_violations(code, self.RID)) >= 1

    def test_positive_dua_fungsi_sangat_mirip(self):
        """Dua fungsi dengan struktur hampir identik → harus terdeteksi."""
        code = """
def proses_data_mahasiswa(data):
    hasil = []
    jumlah = 0
    for item in data:
        if item > 0:
            hasil.append(item * 2)
    return hasil


def proses_data_siswa(data):
    hasil = []
    jumlah = 0
    for item in data:
        if item > 0:
            hasil.append(item * 2)
    return hasil
"""
        assert len(_violations(code, self.RID)) >= 1

    # ── True Negative ──────────────────────────────────────────────────────

    def test_negative_dua_fungsi_berbeda(self):
        """Dua fungsi dengan struktur berbeda → tidak boleh terdeteksi."""
        code = """
def tampilkan_menu():
    print("1. Tambah data")
    print("2. Hapus data")
    print("3. Lihat data")
    print("4. Keluar")


def hitung_statistik(data):
    total = sum(data)
    rata = total / len(data)
    terbesar = max(data)
    terkecil = min(data)
    return rata, terbesar, terkecil
"""
        assert len(_violations(code, self.RID)) == 0

    def test_negative_fungsi_terlalu_pendek(self):
        """Fungsi dengan body < 4 baris dikecualikan dari perbandingan."""
        code = """
def kuadrat(n):
    return n * n


def kubik(n):
    return n * n * n
"""
        assert len(_violations(code, self.RID)) == 0
