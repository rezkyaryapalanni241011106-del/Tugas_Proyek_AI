# ============================================================
# Program Daftar Tugas (To-Do List)
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R03 (LOW)     — fungsi tanpa docstring
#   R09 (LOW)     — print() di dalam fungsi
#   R12 (MEDIUM)  — penggunaan keyword global
#   R13 (CRITICAL)— empty except (except: pass)
#   R14 (CRITICAL)— infinite loop risk (while True tanpa break)
# ============================================================

daftar_tugas = []
tugas_selesai = []
id_tugas = 0


def tambah_tugas(judul, prioritas="normal"):
    global id_tugas      # R12: global
    global daftar_tugas  # R12: global
    id_tugas += 1
    tugas = {
        "id": id_tugas,
        "judul": judul,
        "prioritas": prioritas,
        "selesai": False,
    }
    daftar_tugas.append(tugas)
    print(f"Tugas #{id_tugas} ditambahkan: {judul}")  # R09: print debug
    return id_tugas


def tandai_selesai(id_cari):
    for tugas in daftar_tugas:
        if tugas["id"] == id_cari:
            tugas["selesai"] = True
            tugas_selesai.append(tugas)
            print(f"Tugas #{id_cari} ditandai selesai")  # R09: print debug
            return True
    return False


def hapus_tugas(id_cari):
    global daftar_tugas  # R12: global
    try:
        daftar_tugas = [t for t in daftar_tugas if t["id"] != id_cari]
    except:              # R13: empty except
        pass


def tampilkan_semua():
    if not daftar_tugas:
        print("Tidak ada tugas.")
        return
    for tugas in daftar_tugas:
        status = "✓" if tugas["selesai"] else "○"
        print(f"[{status}] #{tugas['id']} [{tugas['prioritas']}] {tugas['judul']}")


def simpan_ke_file(nama_file):
    try:
        with open(nama_file, "w") as f:
            for tugas in daftar_tugas:
                f.write(f"{tugas['id']},{tugas['judul']},{tugas['prioritas']},{tugas['selesai']}\n")
    except:              # R13: empty except
        pass


def muat_dari_file(nama_file):
    global daftar_tugas  # R12: global
    try:
        with open(nama_file, "r") as f:
            for baris in f:
                bagian = baris.strip().split(",")
                tugas = {
                    "id": int(bagian[0]),
                    "judul": bagian[1],
                    "prioritas": bagian[2],
                    "selesai": bagian[3] == "True",
                }
                daftar_tugas.append(tugas)
    except:              # R13: empty except
        pass


def jalankan_menu_interaktif():
    # R14: while True tanpa break
    while True:
        print("\n=== DAFTAR TUGAS ===")
        print("1. Tambah tugas")
        print("2. Tandai selesai")
        print("3. Hapus tugas")
        print("4. Tampilkan semua")
        pilihan = input("Pilih menu: ")
        if pilihan == "1":
            judul = input("Judul tugas: ")
            tambah_tugas(judul)
        elif pilihan == "2":
            id_t = int(input("ID tugas: "))
            tandai_selesai(id_t)
        elif pilihan == "3":
            id_t = int(input("ID tugas: "))
            hapus_tugas(id_t)
        elif pilihan == "4":
            tampilkan_semua()


if __name__ == "__main__":
    tambah_tugas("Belajar Python", "tinggi")
    tambah_tugas("Mengerjakan PR Matematika", "normal")
    tambah_tugas("Membaca buku AI", "rendah")
    tandai_selesai(1)
    tampilkan_semua()
