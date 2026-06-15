# ============================================================
# Program Sistem Perpustakaan
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R01 (HIGH)    — bare except tanpa tipe
#   R03 (LOW)     — fungsi tanpa docstring
#   R07 (MEDIUM)  — terlalu banyak parameter (>5)
#   R08 (HIGH)    — mutable default argument (list=[])
#   R10 (HIGH)    — fungsi komputasi tanpa return
# ============================================================

koleksi_buku = {}
data_peminjaman = {}
daftar_anggota = {}


def daftarkan_buku(judul, pengarang, isbn, tahun, jumlah_eksemplar=1, tag=[]):
    # R08: tag=[] adalah mutable default argument
    if isbn in koleksi_buku:
        print(f"Buku {isbn} sudah ada")
        return False
    koleksi_buku[isbn] = {
        "judul": judul,
        "pengarang": pengarang,
        "tahun": tahun,
        "eksemplar": jumlah_eksemplar,
        "tersedia": jumlah_eksemplar,
        "tag": tag,
    }
    return True


def daftarkan_anggota(nama, id_anggota, email, alamat="", buku_dipinjam=[]):
    # R08: buku_dipinjam=[] adalah mutable default argument
    daftar_anggota[id_anggota] = {
        "nama": nama,
        "email": email,
        "alamat": alamat,
        "buku": buku_dipinjam,
        "denda": 0,
    }


def pinjam_buku(id_anggota, isbn):
    try:
        if id_anggota not in daftar_anggota:
            return False
        if isbn not in koleksi_buku:
            return False
        if koleksi_buku[isbn]["tersedia"] <= 0:
            return False
        koleksi_buku[isbn]["tersedia"] -= 1
        daftar_anggota[id_anggota]["buku"].append(isbn)
        data_peminjaman[(id_anggota, isbn)] = {"hari": 0}
        return True
    except:           # R01: bare except
        return False


def kembalikan_buku(id_anggota, isbn):
    try:
        if (id_anggota, isbn) not in data_peminjaman:
            return False
        koleksi_buku[isbn]["tersedia"] += 1
        daftar_anggota[id_anggota]["buku"].remove(isbn)
        del data_peminjaman[(id_anggota, isbn)]
        return True
    except:           # R01: bare except
        return False


def laporan_perpustakaan():
    # R06: lebih dari 20 statement
    # R10: ada komputasi tanpa return
    total_buku = len(koleksi_buku)
    total_eksemplar = 0
    total_tersedia = 0
    total_dipinjam = 0
    buku_popular = ""
    max_pinjam = 0
    total_anggota = len(daftar_anggota)
    anggota_aktif = 0
    total_denda = 0

    for isbn, buku in koleksi_buku.items():
        total_eksemplar += buku["eksemplar"]
        total_tersedia += buku["tersedia"]
        dipinjam = buku["eksemplar"] - buku["tersedia"]
        total_dipinjam += dipinjam
        if dipinjam > max_pinjam:
            max_pinjam = dipinjam
            buku_popular = buku["judul"]

    for id_a, anggota in daftar_anggota.items():
        if len(anggota["buku"]) > 0:
            anggota_aktif += 1
        total_denda += anggota["denda"]

    print(f"Total judul buku: {total_buku}")
    print(f"Total eksemplar: {total_eksemplar}")
    print(f"Tersedia: {total_tersedia}, Dipinjam: {total_dipinjam}")
    print(f"Buku paling populer: {buku_popular}")
    print(f"Total anggota: {total_anggota} ({anggota_aktif} aktif meminjam)")
    print(f"Total denda terkumpul: Rp{total_denda:,}")


if __name__ == "__main__":
    daftarkan_buku("Algoritma Pemrograman", "Rinaldi Munir", "978-602-0001", 2020, 3)
    daftarkan_buku("Kecerdasan Buatan", "Sri Hartati", "978-602-0002", 2019, 2)
    daftarkan_anggota("Andi", "A001", "andi@email.com")
    daftarkan_anggota("Budi", "B001", "budi@email.com")
    pinjam_buku("A001", "978-602-0001")
    laporan_perpustakaan()
