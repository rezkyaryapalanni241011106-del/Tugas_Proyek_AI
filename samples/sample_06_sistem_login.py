# ============================================================
# Sistem Login Sederhana
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R03 (LOW)     — fungsi tanpa docstring
#   R11 (MEDIUM)  — hardcoded string berulang ("admin", "aktif")
#   R13 (CRITICAL)— empty except (except: pass)
#   R14 (CRITICAL)— infinite loop risk (while True tanpa break)
# ============================================================

database_pengguna = {
    "admin": {"password": "admin123", "role": "admin", "status": "aktif"},
    "budi": {"password": "budi456", "role": "user", "status": "aktif"},
    "citra": {"password": "citra789", "role": "user", "status": "nonaktif"},
}


def verifikasi_login(username, password):
    if username not in database_pengguna:
        return False
    pengguna = database_pengguna[username]
    if pengguna["password"] != password:
        return False
    # R11: "aktif" muncul berkali-kali, seharusnya jadi konstanta STATUS_AKTIF
    if pengguna["status"] != "aktif":
        return False
    return True


def cek_hak_akses(username, fitur):
    pengguna = database_pengguna.get(username)
    if pengguna is None:
        return False
    # R11: "admin" muncul berkali-kali, seharusnya jadi konstanta ROLE_ADMIN
    if pengguna["role"] == "admin":
        return True
    if fitur == "lihat_data":
        return pengguna["status"] == "aktif"
    return False


def reset_password(username, password_baru):
    try:
        database_pengguna[username]["password"] = password_baru
    except:                     # R13: empty except (menelan error diam-diam)
        pass


def nonaktifkan_akun(username):
    # R11: "nonaktif" berulang — seharusnya jadi konstanta STATUS_NONAKTIF
    if username in database_pengguna:
        database_pengguna[username]["status"] = "nonaktif"


def jalankan_aplikasi():
    # R14: while True tanpa break — risiko infinite loop
    while True:
        print("\n=== SISTEM LOGIN ===")
        username = input("Username: ")
        password = input("Password: ")
        if verifikasi_login(username, password):
            print(f"Selamat datang, {username}!")
            # seharusnya ada kondisi untuk keluar dari loop
        else:
            print("Username atau password salah.")


def daftarkan_pengguna(username, password, role="user"):
    if username in database_pengguna:
        print("Username sudah digunakan")
        return False
    database_pengguna[username] = {
        "password": password,
        "role": role,
        # R11: "aktif" berulang
        "status": "aktif",
    }
    return True


if __name__ == "__main__":
    print("Sistem login siap.")
    print(f"Cek admin: {verifikasi_login('admin', 'admin123')}")
    print(f"Hak akses admin: {cek_hak_akses('admin', 'hapus_data')}")
