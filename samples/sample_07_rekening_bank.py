# ============================================================
# Program Rekening Bank
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R01 (HIGH)    — bare except tanpa tipe
#   R03 (LOW)     — fungsi tanpa docstring
#   R04 (MEDIUM)  — magic number (500000, 50000, 0.05)
#   R05 (HIGH)    — deep nesting (>4 tingkat)
#   R12 (MEDIUM)  — penggunaan keyword global
# ============================================================

total_saldo_bank = 0
jumlah_rekening = 0


def buat_rekening(nama_pemilik, saldo_awal=0):
    global total_saldo_bank   # R12: global
    global jumlah_rekening    # R12: global
    if saldo_awal < 500000:   # R04: 500000 adalah magic number (min saldo)
        return None
    rekening = {
        "pemilik": nama_pemilik,
        "saldo": saldo_awal,
        "riwayat": [],
    }
    total_saldo_bank += saldo_awal
    jumlah_rekening += 1
    return rekening


def transfer(rekening_asal, rekening_tujuan, jumlah):
    # R05: deep nesting — 5+ tingkat if bersarang
    try:
        if rekening_asal is not None:
            if rekening_tujuan is not None:
                if jumlah > 0:
                    if rekening_asal["saldo"] >= jumlah:
                        if jumlah >= 50000:   # R04: 50000 adalah minimum transfer
                            rekening_asal["saldo"] -= jumlah
                            rekening_tujuan["saldo"] += jumlah
                            rekening_asal["riwayat"].append(f"-{jumlah}")
                            rekening_tujuan["riwayat"].append(f"+{jumlah}")
                            return True
    except:                   # R01: bare except
        return False
    return False


def hitung_bunga(rekening):
    saldo = rekening["saldo"]
    # R04: 0.05 adalah magic number (suku bunga 5%)
    bunga = saldo * 0.05
    return bunga


def setor_tunai(rekening, jumlah):
    rekening["saldo"] += jumlah
    rekening["riwayat"].append(f"setor +{jumlah}")


def tarik_tunai(rekening, jumlah):
    if rekening["saldo"] >= jumlah:
        rekening["saldo"] -= jumlah
        rekening["riwayat"].append(f"tarik -{jumlah}")
        return True
    return False


def cek_saldo(rekening):
    return rekening["saldo"]


def tampilkan_riwayat(rekening):
    print(f"Pemilik: {rekening['pemilik']}")
    print(f"Saldo: Rp{rekening['saldo']:,}")
    print("Riwayat transaksi:")
    for transaksi in rekening["riwayat"]:
        print(f"  {transaksi}")


if __name__ == "__main__":
    rek_andi = buat_rekening("Andi", 1000000)
    rek_budi = buat_rekening("Budi", 2000000)

    if rek_andi and rek_budi:
        transfer(rek_andi, rek_budi, 100000)
        tampilkan_riwayat(rek_andi)
        tampilkan_riwayat(rek_budi)
