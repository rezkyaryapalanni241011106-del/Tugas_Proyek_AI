# ============================================================
# Program Kuis Matematika
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R03 (LOW)    — fungsi tanpa docstring
#   R04 (MEDIUM) — magic number (10, 100, 3)
#   R09 (LOW)    — print() di dalam fungsi
#   R15 (HIGH)   — duplikasi kode (generate_soal_* sangat mirip)
# ============================================================

import random


def generate_soal_tambah(level):
    # R15: sangat mirip dengan generate_soal_kurang
    if level == 1:
        a = random.randint(1, 10)   # R04: 10 adalah magic number
        b = random.randint(1, 10)
    elif level == 2:
        a = random.randint(1, 100)  # R04: 100 adalah magic number
        b = random.randint(1, 100)
    else:
        a = random.randint(1, 1000)
        b = random.randint(1, 1000)
    jawaban = a + b
    print(f"[DEBUG] Soal tambah: {a} + {b} = {jawaban}")  # R09: print debug
    return a, b, jawaban


def generate_soal_kurang(level):
    # R15: hampir identik dengan generate_soal_tambah
    if level == 1:
        a = random.randint(1, 10)   # R04: 10 adalah magic number
        b = random.randint(1, 10)
    elif level == 2:
        a = random.randint(1, 100)  # R04: 100 adalah magic number
        b = random.randint(1, 100)
    else:
        a = random.randint(1, 1000)
        b = random.randint(1, 1000)
    if a < b:
        a, b = b, a
    jawaban = a - b
    print(f"[DEBUG] Soal kurang: {a} - {b} = {jawaban}")  # R09: print debug
    return a, b, jawaban


def generate_soal_kali(level):
    if level == 1:
        a = random.randint(1, 10)
        b = random.randint(1, 10)
    else:
        a = random.randint(1, 20)
        b = random.randint(1, 20)
    return a, b, a * b


def minta_jawaban(soal_a, soal_b, operasi):
    print(f"Berapa hasil dari {soal_a} {operasi} {soal_b}?")
    try:
        return int(input("Jawaban: "))
    except ValueError:
        return None


def jalankan_kuis(jumlah_soal=10, level=1):
    # R04: 10 adalah magic number (default jumlah soal)
    # R04: 3 adalah magic number (jumlah jenis operasi)
    skor = 0
    for soal_ke in range(jumlah_soal):
        tipe = random.randint(0, 2)  # R04: 2 adalah magic number
        if tipe == 0:
            a, b, jawaban_benar = generate_soal_tambah(level)
            jawaban = minta_jawaban(a, b, "+")
        elif tipe == 1:
            a, b, jawaban_benar = generate_soal_kurang(level)
            jawaban = minta_jawaban(a, b, "-")
        else:
            a, b, jawaban_benar = generate_soal_kali(level)
            jawaban = minta_jawaban(a, b, "×")

        if jawaban == jawaban_benar:
            print("Benar!")
            skor += 1
        else:
            print(f"Salah! Jawaban yang benar: {jawaban_benar}")

    print(f"\nSkor akhir: {skor}/{jumlah_soal}")
    return skor


if __name__ == "__main__":
    print("=== KUIS MATEMATIKA ===")
    jalankan_kuis(jumlah_soal=5, level=1)
