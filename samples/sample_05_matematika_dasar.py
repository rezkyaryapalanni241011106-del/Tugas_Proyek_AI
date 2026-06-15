# ============================================================
# Operasi Matematika Dasar
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R02 (MEDIUM) — nama variabel tidak deskriptif (a, b, r, h)
#   R03 (LOW)    — fungsi tanpa docstring
#   R04 (MEDIUM) — magic number (3.14, 2, 6)
#   R09 (LOW)    — print() di dalam fungsi
#   R10 (HIGH)   — fungsi komputasi tanpa return
# ============================================================

def luas_lingkaran(r):
    # R02: 'r' adalah nama yang tidak deskriptif untuk radius
    # R04: 3.14 adalah magic number (seharusnya import math atau konstanta PI)
    luas = 3.14 * r * r
    print(f"Menghitung luas dengan r={r}")  # R09: print debug
    return luas


def keliling_lingkaran(r):
    # R04: 2 dan 3.14 adalah magic number
    return 2 * 3.14 * r


def luas_segitiga(a, t):
    # R02: 'a' dan 't' tidak deskriptif (seharusnya alas, tinggi)
    return 0.5 * a * t


def volume_kubus(s):
    # R03: tidak ada docstring
    # R02: 's' tidak deskriptif
    # R04: 3 tidak perlu diberi nama tapi formula kubus memang s^3
    return s * s * s


def hitung_faktorial(n):
    # R10: ada komputasi (for loop dan assignment) tapi tidak ada return
    hasil = 1
    for i in range(1, n + 1):
        hasil *= i
    print(f"Faktorial {n} = {hasil}")  # R09: print debug


def deret_fibonacci(batas):
    # R10: ada assignment dan while tapi tidak ada return
    deret = []
    a, b = 0, 1
    while a <= batas:
        deret.append(a)
        a, b = b, a + b


def cek_bilangan_sempurna(n):
    total = 0
    for i in range(1, n):
        if n % i == 0:
            total += i
    return total == n


def konversi_suhu_celsius_ke_fahrenheit(celsius):
    # R04: 32 dan 9/5 adalah magic number
    return celsius * 9 / 5 + 32


def konversi_suhu_fahrenheit_ke_celsius(fahrenheit):
    # R04: 32 adalah magic number
    return (fahrenheit - 32) * 5 / 9


if __name__ == "__main__":
    print(f"Luas lingkaran r=7: {luas_lingkaran(7):.2f}")
    print(f"Keliling lingkaran r=7: {keliling_lingkaran(7):.2f}")
    print(f"Luas segitiga alas=6, tinggi=4: {luas_segitiga(6, 4)}")
    hitung_faktorial(6)
    deret_fibonacci(50)
