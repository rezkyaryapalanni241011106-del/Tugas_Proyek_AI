# ============================================================
# Program Konverter Satuan
# Kode mahasiswa — mengandung beberapa antipattern
#
# Antipattern yang terdeteksi:
#   R02 (MEDIUM) — nama variabel tidak deskriptif (c, f, k, m, h)
#   R03 (LOW)    — fungsi tanpa docstring
#   R04 (MEDIUM) — magic number (273.15, 1.60934, 0.621371, dsb.)
# ============================================================

def celsius_ke_fahrenheit(c):
    # R02: 'c' tidak deskriptif (seharusnya suhu_celsius)
    # R04: 9, 5, 32 adalah magic number
    f = c * 9 / 5 + 32
    return f


def fahrenheit_ke_celsius(f):
    # R02: 'f' tidak deskriptif (seharusnya suhu_fahrenheit)
    # R04: 32, 5, 9 adalah magic number
    c = (f - 32) * 5 / 9
    return c


def celsius_ke_kelvin(c):
    # R04: 273.15 adalah magic number
    k = c + 273.15
    return k


def kelvin_ke_celsius(k):
    # R02: 'k' tidak deskriptif
    # R04: 273.15 adalah magic number
    return k - 273.15


def km_ke_mil(km):
    # R04: 0.621371 adalah magic number
    return km * 0.621371


def mil_ke_km(m):
    # R02: 'm' tidak deskriptif (seharusnya jarak_mil)
    # R04: 1.60934 adalah magic number
    return m * 1.60934


def kg_ke_pound(kg):
    # R04: 2.20462 adalah magic number
    return kg * 2.20462


def pound_ke_kg(p):
    # R02: 'p' tidak deskriptif
    # R04: 0.453592 adalah magic number
    return p * 0.453592


def liter_ke_galon(liter):
    # R04: 0.264172 adalah magic number
    return liter * 0.264172


def meter_ke_feet(m):
    # R02: 'm' tidak deskriptif
    # R04: 3.28084 adalah magic number
    return m * 3.28084


def jam_ke_menit(h):
    # R02: 'h' tidak deskriptif (seharusnya jumlah_jam)
    # R04: 60 adalah magic number
    return h * 60


def menit_ke_detik(menit):
    # R04: 60 adalah magic number
    return menit * 60


if __name__ == "__main__":
    print("=== KONVERTER SATUAN ===")
    print(f"25°C = {celsius_ke_fahrenheit(25):.1f}°F")
    print(f"77°F = {fahrenheit_ke_celsius(77):.1f}°C")
    print(f"25°C = {celsius_ke_kelvin(25):.2f}K")
    print(f"100 km = {km_ke_mil(100):.2f} mil")
    print(f"70 kg = {kg_ke_pound(70):.2f} pound")
    print(f"2 jam = {jam_ke_menit(2)} menit")
