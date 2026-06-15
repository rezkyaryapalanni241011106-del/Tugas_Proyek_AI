# ============================================================
# Program Analisis Nilai Ujian
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R02 (MEDIUM) — nama variabel tidak deskriptif (s, h, r, d)
#   R03 (LOW)    — fungsi tanpa docstring
#   R05 (HIGH)   — deep nesting (>4 tingkat)
#   R11 (MEDIUM) — hardcoded string berulang ("lulus", "tidak lulus")
#   R12 (MEDIUM) — penggunaan keyword global
# ============================================================

rekap_global = {}
jumlah_siswa_global = 0


def analisis_distribusi(daftar_nilai, mata_pelajaran, kelas, semester, tahun):
    # R05: deep nesting yang berlebihan
    distribusi = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    if daftar_nilai:
        if len(daftar_nilai) > 0:
            for nilai in daftar_nilai:
                if isinstance(nilai, (int, float)):
                    if 0 <= nilai <= 100:
                        if nilai >= 90:
                            distribusi["A"] += 1
                        elif nilai >= 80:
                            distribusi["B"] += 1
                        elif nilai >= 70:
                            distribusi["C"] += 1
                        elif nilai >= 60:
                            distribusi["D"] += 1
                        else:
                            distribusi["E"] += 1
    return distribusi


def hitung_statistik(d):
    # R02: 'd' tidak deskriptif (seharusnya daftar_nilai)
    if not d:
        return {}
    s = sum(d)       # R02: 's' tidak deskriptif
    r = s / len(d)   # R02: 'r' tidak deskriptif (rata-rata)
    h = max(d)       # R02: 'h' tidak deskriptif (tertinggi)
    return {"total": s, "rata": r, "tertinggi": h, "terendah": min(d)}


def kategorikan_siswa(nilai):
    # R11: "lulus" dan "tidak lulus" berulang
    if nilai >= 60:
        status = "lulus"
        keterangan = "Selamat, kamu lulus!"
    else:
        status = "tidak lulus"
        keterangan = "Maaf, kamu tidak lulus."

    # R11: "lulus" muncul lagi di bawah
    if status == "lulus":
        return {"status": "lulus", "keterangan": keterangan, "remedial": False}
    else:
        return {"status": "tidak lulus", "keterangan": keterangan, "remedial": True}


def tambah_rekap(kelas, data):
    global rekap_global        # R12: global
    global jumlah_siswa_global # R12: global
    rekap_global[kelas] = data
    jumlah_siswa_global += len(data.get("nilai", []))


def cetak_laporan(kelas, data_kelas):
    statistik = hitung_statistik(data_kelas.get("nilai", []))
    distribusi = analisis_distribusi(
        data_kelas.get("nilai", []),
        data_kelas.get("mapel", "-"),
        kelas,
        data_kelas.get("semester", 1),
        data_kelas.get("tahun", 2025),
    )
    print(f"\n=== Laporan Kelas {kelas} ===")
    if statistik:
        print(f"Rata-rata: {statistik['rata']:.2f}")
        print(f"Tertinggi: {statistik['tertinggi']}")
        print(f"Terendah:  {statistik['terendah']}")
    print("Distribusi nilai:")
    for grade, jml in distribusi.items():
        print(f"  {grade}: {jml} siswa")


if __name__ == "__main__":
    data_xii_ipa1 = {
        "mapel": "Matematika",
        "semester": 1,
        "tahun": 2025,
        "nilai": [88, 72, 95, 65, 78, 91, 55, 83, 76, 68],
    }
    data_xii_ips2 = {
        "mapel": "Ekonomi",
        "semester": 1,
        "tahun": 2025,
        "nilai": [75, 80, 65, 90, 70, 85, 60, 72, 88, 55],
    }

    tambah_rekap("XII IPA 1", data_xii_ipa1)
    tambah_rekap("XII IPS 2", data_xii_ips2)

    cetak_laporan("XII IPA 1", data_xii_ipa1)
    cetak_laporan("XII IPS 2", data_xii_ips2)
