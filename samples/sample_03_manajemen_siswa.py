# ============================================================
# Program Manajemen Data Siswa
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R03 (LOW)    — fungsi tanpa docstring
#   R06 (MEDIUM) — fungsi terlalu panjang (>20 statement)
#   R07 (MEDIUM) — terlalu banyak parameter (>5)
#   R09 (LOW)    — print() di dalam fungsi
#   R10 (HIGH)   — fungsi komputasi tanpa return
# ============================================================

daftar_siswa = []


def tambah_siswa(nama, nis, kelas, jurusan, nilai_uts, nilai_uas, nilai_tugas, kehadiran):
    # R07: 8 parameter (>5)
    siswa = {
        "nama": nama,
        "nis": nis,
        "kelas": kelas,
        "jurusan": jurusan,
        "nilai_uts": nilai_uts,
        "nilai_uas": nilai_uas,
        "nilai_tugas": nilai_tugas,
        "kehadiran": kehadiran,
    }
    daftar_siswa.append(siswa)
    print(f"Siswa {nama} berhasil ditambahkan")  # R09: print debug


def laporan_lengkap():
    # R06: lebih dari 20 statement dalam satu fungsi
    # R10: ada komputasi tapi tidak ada return
    total_nilai = 0
    jumlah = 0
    nilai_tertinggi = 0
    nama_terbaik = ""
    nilai_terendah = 100
    nama_terburuk = ""
    lulus = 0
    tidak_lulus = 0
    total_kehadiran = 0
    jurusan_ipa = 0
    jurusan_ips = 0
    jurusan_bahasa = 0

    for siswa in daftar_siswa:
        uts = siswa["nilai_uts"]
        uas = siswa["nilai_uas"]
        tugas = siswa["nilai_tugas"]
        rata = (uts * 0.3 + uas * 0.4 + tugas * 0.3)
        total_nilai += rata
        jumlah += 1
        total_kehadiran += siswa["kehadiran"]

        if rata > nilai_tertinggi:
            nilai_tertinggi = rata
            nama_terbaik = siswa["nama"]

        if rata < nilai_terendah:
            nilai_terendah = rata
            nama_terburuk = siswa["nama"]

        if rata >= 60:
            lulus += 1
        else:
            tidak_lulus += 1

        if siswa["jurusan"] == "IPA":
            jurusan_ipa += 1
        elif siswa["jurusan"] == "IPS":
            jurusan_ips += 1
        else:
            jurusan_bahasa += 1

    rata_kelas = total_nilai / jumlah if jumlah > 0 else 0
    rata_kehadiran = total_kehadiran / jumlah if jumlah > 0 else 0

    print(f"Jumlah siswa: {jumlah}")
    print(f"Rata-rata kelas: {rata_kelas:.2f}")
    print(f"Nilai tertinggi: {nilai_tertinggi:.2f} ({nama_terbaik})")
    print(f"Nilai terendah: {nilai_terendah:.2f} ({nama_terburuk})")
    print(f"Lulus: {lulus}, Tidak lulus: {tidak_lulus}")
    print(f"Rata-rata kehadiran: {rata_kehadiran:.1f}%")


def cari_siswa(keyword):
    hasil = []
    for siswa in daftar_siswa:
        if keyword.lower() in siswa["nama"].lower():
            hasil.append(siswa)
    return hasil


def hapus_siswa(nis):
    for i, siswa in enumerate(daftar_siswa):
        if siswa["nis"] == nis:
            daftar_siswa.pop(i)
            print(f"Siswa dengan NIS {nis} dihapus")  # R09: print debug
            return
    print(f"Siswa dengan NIS {nis} tidak ditemukan")


if __name__ == "__main__":
    tambah_siswa("Andi", "001", "XII IPA 1", "IPA", 85, 88, 90, 95)
    tambah_siswa("Budi", "002", "XII IPA 1", "IPA", 70, 72, 75, 88)
    tambah_siswa("Citra", "003", "XII IPS 2", "IPS", 55, 60, 65, 80)
    laporan_lengkap()
