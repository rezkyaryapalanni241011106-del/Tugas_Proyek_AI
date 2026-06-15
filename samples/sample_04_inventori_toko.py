# ============================================================
# Program Inventori Toko Sederhana
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R03 (LOW)    — fungsi tanpa docstring
#   R04 (MEDIUM) — magic number (1000, 0.1, 30)
#   R08 (HIGH)   — mutable default argument (list=[])
#   R15 (HIGH)   — duplikasi kode (dua fungsi sangat mirip)
# ============================================================

stok_barang = {}


def tambah_produk(nama, harga, jumlah, kategori="umum", daftar_promo=[]):
    # R08: daftar_promo=[] adalah mutable default
    stok_barang[nama] = {
        "harga": harga,
        "jumlah": jumlah,
        "kategori": kategori,
        "promo": daftar_promo,
    }


def hitung_nilai_stok_elektronik(barang_list):
    # R15: sangat mirip dengan hitung_nilai_stok_makanan
    total = 0
    jumlah_item = 0
    for nama in barang_list:
        if nama in stok_barang:
            data = stok_barang[nama]
            total += data["harga"] * data["jumlah"]
            jumlah_item += data["jumlah"]
    rata = total / jumlah_item if jumlah_item > 0 else 0
    return total, rata


def hitung_nilai_stok_makanan(barang_list):
    # R15: hampir identik dengan hitung_nilai_stok_elektronik
    total = 0
    jumlah_item = 0
    for nama in barang_list:
        if nama in stok_barang:
            data = stok_barang[nama]
            total += data["harga"] * data["jumlah"]
            jumlah_item += data["jumlah"]
    rata = total / jumlah_item if jumlah_item > 0 else 0
    return total, rata


def cek_stok_minimum():
    barang_habis = []
    for nama, data in stok_barang.items():
        if data["jumlah"] < 30:   # R04: magic number 30
            barang_habis.append(nama)
    return barang_habis


def hitung_diskon(harga):
    # R04: 0.1 adalah magic number (seharusnya DISKON = 0.1)
    return harga * 0.1


def update_harga_batch(kenaikan_persen):
    for nama in stok_barang:
        harga_lama = stok_barang[nama]["harga"]
        stok_barang[nama]["harga"] = harga_lama * (1 + kenaikan_persen / 100)
        if stok_barang[nama]["harga"] < 1000:  # R04: magic number 1000
            stok_barang[nama]["harga"] = 1000


if __name__ == "__main__":
    tambah_produk("Laptop", 8500000, 10, "elektronik")
    tambah_produk("Mouse", 150000, 50, "elektronik")
    tambah_produk("Beras 5kg", 65000, 100, "makanan")
    tambah_produk("Minyak Goreng", 28000, 25, "makanan")

    elektronik = ["Laptop", "Mouse"]
    makanan = ["Beras 5kg", "Minyak Goreng"]

    total_el, rata_el = hitung_nilai_stok_elektronik(elektronik)
    total_mk, rata_mk = hitung_nilai_stok_makanan(makanan)

    print(f"Nilai stok elektronik: Rp{total_el:,}")
    print(f"Nilai stok makanan: Rp{total_mk:,}")
    print(f"Barang hampir habis: {cek_stok_minimum()}")
