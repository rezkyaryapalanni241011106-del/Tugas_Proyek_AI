# ============================================================
# Kalkulator Sederhana
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R01 (HIGH)   — bare except tanpa tipe exception
#   R03 (LOW)    — fungsi tanpa docstring
#   R04 (MEDIUM) — magic number (100, 25000, 0.11)
#   R09 (LOW)    — print() di dalam fungsi
#   R12 (MEDIUM) — penggunaan keyword global
# ============================================================

total_transaksi = 0


def tambah(a, b):
    return a + b


def kurang(a, b):
    return a - b


def kali(a, b):
    return a * b


def bagi(angka1, angka2):
    try:
        hasil = angka1 / angka2
        return hasil
    except:
        print("Tidak bisa dibagi nol!")
        return 0


def hitung_diskon(harga, persen):
    # R04: magic number 100
    diskon = harga * persen / 100
    return harga - diskon


def hitung_ppn(harga):
    # R04: 0.11 adalah magic number (seharusnya PPN = 0.11)
    return harga * 1.11


def hitung_gaji(jam_kerja):
    global total_transaksi  # R12: global
    tarif_per_jam = 25000   # R04: magic number
    gaji = jam_kerja * tarif_per_jam
    total_transaksi += gaji
    print(f"Gaji dihitung: Rp{gaji}")  # R09: print debug
    return gaji


def tampilkan_menu():
    print("=== KALKULATOR SEDERHANA ===")
    print("1. Tambah")
    print("2. Kurang")
    print("3. Kali")
    print("4. Bagi")
    print("5. Keluar")


if __name__ == "__main__":
    tampilkan_menu()
    pilihan = int(input("Pilih operasi: "))
    if pilihan in [1, 2, 3, 4]:
        angka1 = float(input("Angka pertama: "))
        angka2 = float(input("Angka kedua: "))
        if pilihan == 1:
            print(f"Hasil: {tambah(angka1, angka2)}")
        elif pilihan == 2:
            print(f"Hasil: {kurang(angka1, angka2)}")
        elif pilihan == 3:
            print(f"Hasil: {kali(angka1, angka2)}")
        elif pilihan == 4:
            print(f"Hasil: {bagi(angka1, angka2)}")
