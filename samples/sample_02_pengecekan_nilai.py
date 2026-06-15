# ============================================================
# Program Pengecekan Nilai Mahasiswa
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R03 (LOW)    — fungsi tanpa docstring
#   R04 (MEDIUM) — magic number (90, 80, 70, 60)
#   R10 (HIGH)   — fungsi melakukan komputasi tanpa return
#   R12 (MEDIUM) — penggunaan keyword global
#   R13 (CRITICAL)— empty except (except: pass)
# ============================================================

total_nilai = 0
jumlah_mahasiswa = 0


def konversi_huruf(nilai):
    if nilai >= 90:    # R04: magic number
        return "A"
    elif nilai >= 80:  # R04: magic number
        return "B"
    elif nilai >= 70:  # R04: magic number
        return "C"
    elif nilai >= 60:  # R04: magic number
        return "D"
    else:
        return "E"


def tambah_nilai(nilai):
    global total_nilai          # R12: global
    global jumlah_mahasiswa     # R12: global
    total_nilai += nilai
    jumlah_mahasiswa += 1


def hitung_rata_rata():
    # R10: ada komputasi tapi tidak ada return
    rata = total_nilai / jumlah_mahasiswa


def baca_nilai_dari_file(nama_file):
    daftar_nilai = []
    try:
        with open(nama_file, "r") as f:
            for baris in f:
                nilai = int(baris.strip())
                daftar_nilai.append(nilai)
    except:                # R13: empty except
        pass
    return daftar_nilai


def cetak_hasil(daftar_nilai):
    for nilai in daftar_nilai:
        huruf = konversi_huruf(nilai)
        print(f"Nilai: {nilai} → Grade: {huruf}")


if __name__ == "__main__":
    data = [85, 72, 91, 65, 78, 88, 55, 93]
    for nilai in data:
        tambah_nilai(nilai)
    hitung_rata_rata()
    cetak_hasil(data)
