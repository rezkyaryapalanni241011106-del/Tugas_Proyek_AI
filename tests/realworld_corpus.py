"""
realworld_corpus.py — ~200 program Python REALISTIS untuk audit analyzer.

Tujuan: menguji perilaku analyzer pada kode yang ditulis "seperti programmer
biasa" (bukan kode yang sengaja direkayasa untuk memicu rule tertentu).

Konvensi label:
  expect = rule yang SEHARUSNYA muncul (cek false-negative).
  forbid = rule yang TIDAK boleh muncul (cek false-positive). Dihitung otomatis
           = STRUCT - expect. STRUCT sengaja TIDAK memasukkan R03 & R04 karena
           keduanya "agresif by design" (R03: fungsi >=5 statement tanpa
           docstring; R04: SETIAP angka selain 0/1/-1) — kemunculannya dicatat
           sebagai info, bukan kegagalan. R03/R04 tetap boleh ditaruh di
           `expect` untuk memastikan ia memang muncul.
"""

# ---- ID rule (hindari salah ketik) ----
R01 = "R01_bare_except"
R02 = "R02_non_descriptive_name"
R03 = "R03_missing_docstring"
R04 = "R04_magic_number"
R05 = "R05_deep_nesting"
R06 = "R06_long_function"
R07 = "R07_too_many_params"
R08 = "R08_mutable_default"
R09 = "R09_print_debug"
R10 = "R10_no_return"
R11 = "R11_hardcoded_string"
R12 = "R12_global_variable"
R13 = "R13_empty_except"
R14 = "R14_infinite_loop_risk"
R15 = "R15_code_duplication"

# Rule "struktural/perilaku" yang seharusnya jarang salah-picu pada kode bersih.
# Sengaja TANPA R03 & R04 (lihat docstring).
STRUCT = {R01, R02, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R15}

SAMPLES = []


def add(name, category, code, expect=(), forbid=None, syntax_error=False):
    expect = set(expect)
    if forbid is None:
        forbid = STRUCT - expect
    SAMPLES.append({
        "name": name,
        "category": category,
        "code": code.strip("\n") + "\n",
        "expect": expect,
        "forbid": set(forbid),
        "syntax_error": syntax_error,
    })


# ============================================================
# 1) MATEMATIKA & NUMERIK
# ============================================================

add("circle_area", "math", """
import math


def circle_area(radius):
    \"\"\"Hitung luas lingkaran.\"\"\"
    return math.pi * radius * radius
""")

add("rectangle_area", "math", """
def rectangle_area(length, width):
    \"\"\"Luas persegi panjang.\"\"\"
    return length * width
""")

add("average", "math", """
def average(numbers):
    \"\"\"Rata-rata sebuah list angka.\"\"\"
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
""")

add("celsius_to_fahrenheit", "math", """
def celsius_to_fahrenheit(celsius):
    \"\"\"Konversi Celsius ke Fahrenheit.\"\"\"
    return celsius * 9 / 5 + 32
""", expect={R04})

add("hitung_bmi", "math", """
def hitung_bmi(berat, tinggi):
    \"\"\"Hitung Body Mass Index.\"\"\"
    return berat / (tinggi * tinggi)
""")

add("faktorial_iter", "math", """
def faktorial(n):
    \"\"\"Faktorial n secara iteratif.\"\"\"
    hasil = 1
    for i in range(2, n + 1):
        hasil = hasil * i
    return hasil
""")

add("is_prime", "math", """
def is_prime(number):
    \"\"\"Cek apakah sebuah bilangan adalah prima.\"\"\"
    if number < 2:
        return False
    for divisor in range(2, number):
        if number % divisor == 0:
            return False
    return True
""", expect={R04})

add("fibonacci_list", "math", """
def fibonacci(n):
    \"\"\"Kembalikan list n bilangan Fibonacci pertama.\"\"\"
    deret = [0, 1]
    for i in range(2, n):
        deret.append(deret[i - 1] + deret[i - 2])
    return deret
""", expect={R04})

add("pangkat_rekursif", "math", """
def pangkat(base, exponent):
    \"\"\"Hitung base pangkat exponent secara rekursif.\"\"\"
    if exponent == 0:
        return 1
    return base * pangkat(base, exponent - 1)
""")

add("gcd_euclid", "math", """
def gcd(a, b):
    \"\"\"Faktor persekutuan terbesar (algoritma Euclid).\"\"\"
    while b:
        a, b = b, a % b
    return a
""", expect={R02})

add("clamp_value", "math", """
def clamp(value, low, high):
    \"\"\"Batasi value agar berada di rentang [low, high].\"\"\"
    if value < low:
        return low
    if value > high:
        return high
    return value
""")

add("persentase", "math", """
def persentase(bagian, total):
    \"\"\"Hitung persentase bagian terhadap total.\"\"\"
    if total == 0:
        return 0
    return bagian / total * 100
""", expect={R04})

add("bunga_majemuk", "math", """
def bunga_majemuk(pokok, rate, tahun):
    \"\"\"Hitung nilai akhir investasi dengan bunga majemuk.\"\"\"
    return pokok * (1 + rate) ** tahun
""")

add("jarak_euclidean", "math", """
import math


def jarak(x1, y1, x2, y2):
    \"\"\"Jarak Euclidean antara dua titik.\"\"\"
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
""", expect={R04})

add("akar_kuadrat", "math", """
import math


def akar_kuadrat(a, b, c):
    \"\"\"Cari akar persamaan kuadrat ax^2+bx+c.\"\"\"
    diskriminan = b * b - 4 * a * c
    if diskriminan < 0:
        return None
    akar1 = (-b + math.sqrt(diskriminan)) / (2 * a)
    akar2 = (-b - math.sqrt(diskriminan)) / (2 * a)
    return akar1, akar2
""", expect={R02, R04})

add("is_genap", "math", """
def is_genap(angka):
    \"\"\"True jika angka genap.\"\"\"
    return angka % 2 == 0
""", expect={R04})

add("jumlah_digit", "math", """
def jumlah_digit(angka):
    \"\"\"Jumlahkan semua digit dari sebuah bilangan.\"\"\"
    total = 0
    while angka > 0:
        total = total + angka % 10
        angka = angka // 10
    return total
""", expect={R04})

add("maksimum_tiga", "math", """
def maksimum_tiga(a, b, c):
    \"\"\"Kembalikan nilai terbesar dari tiga angka.\"\"\"
    terbesar = a
    if b > terbesar:
        terbesar = b
    if c > terbesar:
        terbesar = c
    return terbesar
""", expect={R02})

add("rata_rata_manual", "math", """
def rata_rata(data):
    \"\"\"Hitung rata-rata aritmetik.\"\"\"
    jumlah = 0
    for nilai in data:
        jumlah = jumlah + nilai
    return jumlah / len(data)
""")

add("nilai_absolut", "math", """
def nilai_absolut(angka):
    \"\"\"Kembalikan nilai absolut tanpa fungsi bawaan.\"\"\"
    if angka < 0:
        return -angka
    return angka
""")

# ============================================================
# 2) STRING & TEKS
# ============================================================

add("reverse_string", "string", """
def reverse_string(text):
    \"\"\"Balik urutan karakter dalam string.\"\"\"
    return text[::-1]
""")

add("count_vowels", "string", """
def count_vowels(text):
    \"\"\"Hitung jumlah huruf vokal dalam teks.\"\"\"
    vokal = "aeiou"
    jumlah = 0
    for huruf in text.lower():
        if huruf in vokal:
            jumlah = jumlah + 1
    return jumlah
""")

add("is_palindrome", "string", """
def is_palindrome(text):
    \"\"\"Cek apakah teks adalah palindrom.\"\"\"
    bersih = text.lower().replace(" ", "")
    return bersih == bersih[::-1]
""")

add("kapital_kata", "string", """
def kapital_setiap_kata(kalimat):
    \"\"\"Ubah huruf pertama tiap kata jadi kapital.\"\"\"
    kata_list = kalimat.split(" ")
    hasil = []
    for kata in kata_list:
        hasil.append(kata.capitalize())
    return " ".join(hasil)
""")

add("hitung_kata", "string", """
def hitung_kata(kalimat):
    \"\"\"Hitung jumlah kata dalam kalimat.\"\"\"
    if not kalimat.strip():
        return 0
    return len(kalimat.split())
""")

add("caesar_cipher", "string", """
def caesar_cipher(teks, geser):
    \"\"\"Enkripsi teks sederhana dengan Caesar cipher.\"\"\"
    hasil = ""
    for huruf in teks:
        kode = ord(huruf) + geser
        hasil = hasil + chr(kode)
    return hasil
""")

add("slugify", "string", """
def slugify(judul):
    \"\"\"Ubah judul menjadi slug URL.\"\"\"
    slug = judul.lower().strip()
    slug = slug.replace(" ", "-")
    return slug
""")

add("hitung_karakter", "string", """
def hitung_karakter(teks, target):
    \"\"\"Hitung kemunculan karakter target.\"\"\"
    jumlah = 0
    for huruf in teks:
        if huruf == target:
            jumlah = jumlah + 1
    return jumlah
""")

add("is_anagram", "string", """
def is_anagram(kata1, kata2):
    \"\"\"Cek apakah dua kata saling anagram.\"\"\"
    return sorted(kata1.lower()) == sorted(kata2.lower())
""")

add("potong_teks", "string", """
def potong_teks(teks, batas):
    \"\"\"Potong teks bila melebihi batas, tambahkan elipsis.\"\"\"
    if len(teks) <= batas:
        return teks
    return teks[:batas] + "..."
""")

add("frekuensi_kata", "string", """
def frekuensi_kata(kalimat):
    \"\"\"Hitung frekuensi tiap kata dalam kalimat.\"\"\"
    frekuensi = {}
    for kata in kalimat.lower().split():
        frekuensi[kata] = frekuensi.get(kata, 0) + 1
    return frekuensi
""")

add("kata_terpanjang", "string", """
def kata_terpanjang(kalimat):
    \"\"\"Cari kata terpanjang dalam kalimat.\"\"\"
    kata_list = kalimat.split()
    terpanjang = ""
    for kata in kata_list:
        if len(kata) > len(terpanjang):
            terpanjang = kata
    return terpanjang
""")

add("judul_kapital", "string", """
def judul_kapital(teks):
    \"\"\"Kapitalkan tiap awal kata memakai title().\"\"\"
    return teks.title()
""")

add("sensor_kata", "string", """
def sensor_kata(kalimat, kata_kotor):
    \"\"\"Ganti kata terlarang dengan tanda bintang.\"\"\"
    bintang = "*" * len(kata_kotor)
    return kalimat.replace(kata_kotor, bintang)
""")

add("inisial", "string", """
def inisial(nama_lengkap):
    \"\"\"Ambil inisial dari nama lengkap.\"\"\"
    bagian = nama_lengkap.split()
    huruf = []
    for kata in bagian:
        huruf.append(kata[0].upper())
    return ".".join(huruf)
""")

add("ulang_teks_debug", "string", """
def ulang_teks(teks, kali):
    \"\"\"Ulang teks beberapa kali (versi debug).\"\"\"
    hasil = teks * kali
    print("debug:", hasil)
    return hasil
""", expect={R09})

add("ke_list_angka", "string", """
def ke_list_angka(teks):
    \"\"\"Ubah '1,2,3' menjadi list integer.\"\"\"
    bagian = teks.split(",")
    angka = []
    for item in bagian:
        angka.append(int(item))
    return angka
""")

add("mask_email", "string", """
def mask_email(email):
    \"\"\"Sembunyikan sebagian alamat email.\"\"\"
    nama, domain = email.split("@")
    return nama[0] + "***@" + domain
""")

add("hitung_baris", "string", """
def hitung_baris(teks):
    \"\"\"Hitung jumlah baris non-kosong.\"\"\"
    jumlah = 0
    for baris in teks.split("\\n"):
        if baris.strip():
            jumlah = jumlah + 1
    return jumlah
""")

add("rata_kanan", "string", """
def rata_kanan(teks, lebar):
    \"\"\"Tambahkan spasi di kiri agar teks rata kanan.\"\"\"
    kurang = lebar - len(teks)
    if kurang <= 0:
        return teks
    return " " * kurang + teks
""")

# ============================================================
# 3) LIST & KOLEKSI
# ============================================================

add("jumlahkan_list", "list", """
def jumlahkan(angka_list):
    \"\"\"Jumlahkan semua elemen list.\"\"\"
    total = 0
    for angka in angka_list:
        total = total + angka
    return total
""")

add("cari_maksimum", "list", """
def cari_maksimum(data):
    \"\"\"Cari nilai maksimum tanpa fungsi bawaan.\"\"\"
    if not data:
        return None
    maksimum = data[0]
    for nilai in data:
        if nilai > maksimum:
            maksimum = nilai
    return maksimum
""")

add("hapus_duplikat", "list", """
def hapus_duplikat(data):
    \"\"\"Hapus elemen duplikat, pertahankan urutan.\"\"\"
    unik = []
    for item in data:
        if item not in unik:
            unik.append(item)
    return unik
""")

add("ratakan_nested", "list", """
def ratakan(nested):
    \"\"\"Ratakan list dua dimensi menjadi satu dimensi.\"\"\"
    hasil = []
    for baris in nested:
        for item in baris:
            hasil.append(item)
    return hasil
""")

add("bagi_kelompok", "list", """
def bagi_kelompok(data, ukuran):
    \"\"\"Bagi list menjadi kelompok berukuran 'ukuran'.\"\"\"
    kelompok = []
    for i in range(0, len(data), ukuran):
        kelompok.append(data[i:i + ukuran])
    return kelompok
""")

add("terbesar_kedua", "list", """
def terbesar_kedua(data):
    \"\"\"Cari nilai terbesar kedua dalam list.\"\"\"
    unik = sorted(set(data))
    if len(unik) < 2:
        return None
    return unik[-2]
""", expect={R04})

add("putar_list", "list", """
def putar_list(data, n):
    \"\"\"Putar elemen list ke kanan sebanyak n.\"\"\"
    if not data:
        return data
    n = n % len(data)
    return data[-n:] + data[:n]
""")

add("total_berjalan", "list", """
def total_berjalan(data):
    \"\"\"Kembalikan list total kumulatif.\"\"\"
    hasil = []
    berjalan = 0
    for nilai in data:
        berjalan = berjalan + nilai
        hasil.append(berjalan)
    return hasil
""")

add("saring_genap", "list", """
def saring_genap(data):
    \"\"\"Ambil hanya angka genap dari list.\"\"\"
    return [angka for angka in data if angka % 2 == 0]
""", expect={R04})

add("gabung_terurut", "list", """
def gabung_terurut(a, b):
    \"\"\"Gabungkan dua list terurut menjadi satu list terurut.\"\"\"
    hasil = []
    i = 0
    j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            hasil.append(a[i])
            i = i + 1
        else:
            hasil.append(b[j])
            j = j + 1
    return hasil + a[i:] + b[j:]
""", expect={R02})

add("hitung_kemunculan", "list", """
def hitung_kemunculan(data, target):
    \"\"\"Hitung berapa kali target muncul dalam list.\"\"\"
    jumlah = 0
    for item in data:
        if item == target:
            jumlah = jumlah + 1
    return jumlah
""")

add("irisan", "list", """
def irisan(a, b):
    \"\"\"Cari elemen yang ada di kedua list.\"\"\"
    return [item for item in a if item in b]
""", expect={R02})

add("rata_bergerak", "list", """
def rata_bergerak(data, jendela):
    \"\"\"Hitung rata-rata bergerak dengan ukuran jendela.\"\"\"
    hasil = []
    for i in range(len(data) - jendela + 1):
        potongan = data[i:i + jendela]
        hasil.append(sum(potongan) / len(potongan))
    return hasil
""")

add("kelompokkan_paritas", "list", """
def kelompokkan_paritas(data):
    \"\"\"Pisahkan angka genap dan ganjil ke dua list.\"\"\"
    genap = []
    ganjil = []
    for angka in data:
        if angka % 2 == 0:
            genap.append(angka)
        else:
            ganjil.append(angka)
    return genap, ganjil
""", expect={R04})

add("dot_product", "list", """
def dot_product(a, b):
    \"\"\"Hitung hasil kali titik dua vektor.\"\"\"
    total = 0
    for i in range(len(a)):
        total = total + a[i] * b[i]
    return total
""", expect={R02})

add("min_maks", "list", """
def min_maks(data):
    \"\"\"Kembalikan nilai minimum dan maksimum sekaligus.\"\"\"
    minimum = data[0]
    maksimum = data[0]
    for nilai in data:
        if nilai < minimum:
            minimum = nilai
        if nilai > maksimum:
            maksimum = nilai
    return minimum, maksimum
""")

add("ke_kamus", "list", """
def ke_kamus(kunci_list, nilai_list):
    \"\"\"Pasangkan dua list menjadi kamus.\"\"\"
    kamus = {}
    for i in range(len(kunci_list)):
        kamus[kunci_list[i]] = nilai_list[i]
    return kamus
""")

add("maks_kumulatif", "list", """
def maks_kumulatif(data):
    \"\"\"Kembalikan list maksimum kumulatif.\"\"\"
    hasil = []
    tertinggi = data[0]
    for nilai in data:
        if nilai > tertinggi:
            tertinggi = nilai
        hasil.append(tertinggi)
    return hasil
""")

add("rata_aman", "list", """
def rata_aman(data):
    \"\"\"Rata-rata list, kembalikan 0 jika kosong.\"\"\"
    if len(data) == 0:
        return 0
    return sum(data) / len(data)
""")

add("balik_di_tempat", "list", """
def balik_di_tempat(data):
    \"\"\"Balik urutan list secara in-place.\"\"\"
    kiri = 0
    kanan = len(data) - 1
    while kiri < kanan:
        data[kiri], data[kanan] = data[kanan], data[kiri]
        kiri = kiri + 1
        kanan = kanan - 1
""")

# ============================================================
# 4) OOP / KELAS
# ============================================================

add("kelas_rectangle", "oop", """
class Rectangle:
    \"\"\"Persegi panjang dengan lebar dan tinggi.\"\"\"

    def __init__(self, lebar, tinggi):
        self.lebar = lebar
        self.tinggi = tinggi

    def luas(self):
        \"\"\"Kembalikan luas.\"\"\"
        return self.lebar * self.tinggi

    def keliling(self):
        \"\"\"Kembalikan keliling.\"\"\"
        return 2 * (self.lebar + self.tinggi)
""", expect={R04})

add("kelas_rekening", "oop", """
class RekeningBank:
    \"\"\"Rekening bank sederhana.\"\"\"

    def __init__(self, pemilik, saldo):
        self.pemilik = pemilik
        self.saldo = saldo

    def setor(self, jumlah):
        \"\"\"Tambah saldo.\"\"\"
        self.saldo = self.saldo + jumlah
        return self.saldo

    def tarik(self, jumlah):
        \"\"\"Kurangi saldo bila cukup.\"\"\"
        if jumlah > self.saldo:
            return False
        self.saldo = self.saldo - jumlah
        return True
""")

add("kelas_stack", "oop", """
class Stack:
    \"\"\"Tumpukan LIFO sederhana.\"\"\"

    def __init__(self):
        self.data = []

    def push(self, item):
        \"\"\"Tambahkan item ke atas tumpukan.\"\"\"
        self.data.append(item)

    def pop(self):
        \"\"\"Ambil item teratas.\"\"\"
        if not self.data:
            return None
        return self.data.pop()

    def is_empty(self):
        \"\"\"True jika tumpukan kosong.\"\"\"
        return len(self.data) == 0
""")

add("kelas_queue", "oop", """
class Queue:
    \"\"\"Antrian FIFO sederhana.\"\"\"

    def __init__(self):
        self.data = []

    def enqueue(self, item):
        \"\"\"Tambahkan item ke belakang antrian.\"\"\"
        self.data.append(item)

    def dequeue(self):
        \"\"\"Ambil item terdepan.\"\"\"
        if not self.data:
            return None
        return self.data.pop(0)
""")

add("kelas_penghitung", "oop", """
class Penghitung:
    \"\"\"Penghitung yang bisa dinaikkan dan direset.\"\"\"

    def __init__(self):
        self.nilai = 0

    def naik(self):
        \"\"\"Naikkan satu.\"\"\"
        self.nilai = self.nilai + 1
        return self.nilai

    def reset(self):
        \"\"\"Kembalikan ke nol.\"\"\"
        self.nilai = 0
""")

add("kelas_circle", "oop", """
import math


class Circle:
    \"\"\"Lingkaran dengan jari-jari tertentu.\"\"\"

    def __init__(self, jari):
        self.jari = jari

    def luas(self):
        \"\"\"Luas lingkaran.\"\"\"
        return math.pi * self.jari * self.jari

    def keliling(self):
        \"\"\"Keliling lingkaran.\"\"\"
        return 2 * math.pi * self.jari
""", expect={R04})

add("kelas_point", "oop", """
import math


class Point:
    \"\"\"Titik 2D.\"\"\"

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def jarak_ke(self, lain):
        \"\"\"Jarak Euclidean ke titik lain.\"\"\"
        dx = self.x - lain.x
        dy = self.y - lain.y
        return math.sqrt(dx * dx + dy * dy)
""")

add("kelas_mahasiswa", "oop", """
class Mahasiswa:
    \"\"\"Data mahasiswa dan nilainya.\"\"\"

    def __init__(self, nama):
        self.nama = nama
        self.nilai = []

    def tambah_nilai(self, n):
        \"\"\"Tambahkan satu nilai.\"\"\"
        self.nilai.append(n)

    def rata_rata(self):
        \"\"\"Rata-rata semua nilai.\"\"\"
        if not self.nilai:
            return 0
        return sum(self.nilai) / len(self.nilai)
""")

add("kelas_keranjang", "oop", """
class Keranjang:
    \"\"\"Keranjang belanja dengan daftar harga.\"\"\"

    def __init__(self):
        self.items = []

    def tambah(self, harga):
        \"\"\"Tambahkan harga item.\"\"\"
        self.items.append(harga)

    def total_dengan_pajak(self):
        \"\"\"Total termasuk pajak 11 persen.\"\"\"
        subtotal = sum(self.items)
        pajak = subtotal * 0.11
        return subtotal + pajak
""", expect={R04})

add("kelas_timer", "oop", """
import time


class Timer:
    \"\"\"Stopwatch sederhana.\"\"\"

    def __init__(self):
        self.mulai = None

    def start(self):
        \"\"\"Mulai menghitung, kembalikan waktu mulai.\"\"\"
        self.mulai = time.time()
        return self.mulai

    def elapsed(self):
        \"\"\"Detik yang berlalu sejak start.\"\"\"
        if self.mulai is None:
            return 0
        return time.time() - self.mulai
""")

add("kelas_hewan_warisan", "oop", """
class Hewan:
    \"\"\"Kelas dasar hewan.\"\"\"

    def __init__(self, nama):
        self.nama = nama

    def suara(self):
        \"\"\"Suara default.\"\"\"
        return "..."


class Kucing(Hewan):
    \"\"\"Kucing yang mengeong.\"\"\"

    def suara(self):
        \"\"\"Suara kucing.\"\"\"
        return "Meong"
""")

add("kelas_produk", "oop", """
class Produk:
    \"\"\"Produk dengan stok.\"\"\"

    def __init__(self, nama, stok):
        self.nama = nama
        self.stok = stok

    def kurangi(self, jumlah):
        \"\"\"Kurangi stok bila mencukupi.\"\"\"
        if jumlah > self.stok:
            return False
        self.stok = self.stok - jumlah
        return True
""")

add("kelas_suhu", "oop", """
class Suhu:
    \"\"\"Suhu dengan konversi satuan.\"\"\"

    def __init__(self, celsius):
        self.celsius = celsius

    def ke_fahrenheit(self):
        \"\"\"Konversi ke Fahrenheit.\"\"\"
        return self.celsius * 9 / 5 + 32

    def ke_kelvin(self):
        \"\"\"Konversi ke Kelvin.\"\"\"
        return self.celsius + 273.15
""", expect={R04})

add("kelas_playlist", "oop", """
import random


class Playlist:
    \"\"\"Daftar putar lagu.\"\"\"

    def __init__(self):
        self.lagu = []

    def tambah(self, judul):
        \"\"\"Tambahkan lagu.\"\"\"
        self.lagu.append(judul)

    def acak(self):
        \"\"\"Acak urutan lagu.\"\"\"
        random.shuffle(self.lagu)
        return self.lagu
""")

add("kelas_kalkulator_log", "oop", """
class Kalkulator:
    \"\"\"Kalkulator dengan log.\"\"\"

    def __init__(self):
        self.terakhir = 0

    def tambah(self, a, b):
        \"\"\"Jumlahkan dan catat hasil.\"\"\"
        hasil = a + b
        print("hasil tambah:", hasil)
        self.terakhir = hasil
        return hasil
""", expect={R02, R09})

add("kelas_konfigurasi", "oop", """
class Konfigurasi:
    \"\"\"Pembaca konfigurasi sederhana.\"\"\"

    def __init__(self, data):
        self.data = data

    def ambil(self, kunci):
        \"\"\"Ambil nilai, abaikan error.\"\"\"
        try:
            return self.data[kunci]
        except:
            return None
""", expect={R01})

# ============================================================
# 5) ALGORITMA (sorting / searching)
# ============================================================

add("bubble_sort", "algo", """
def bubble_sort(data):
    \"\"\"Urutkan list dengan bubble sort (in-place).\"\"\"
    n = len(data)
    for i in range(n):
        for j in range(n - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data
""")

add("selection_sort", "algo", """
def selection_sort(data):
    \"\"\"Urutkan list dengan selection sort.\"\"\"
    n = len(data)
    for i in range(n):
        terkecil = i
        for j in range(i + 1, n):
            if data[j] < data[terkecil]:
                terkecil = j
        data[i], data[terkecil] = data[terkecil], data[i]
    return data
""")

add("insertion_sort", "algo", """
def insertion_sort(data):
    \"\"\"Urutkan list dengan insertion sort.\"\"\"
    for i in range(1, len(data)):
        kunci = data[i]
        j = i - 1
        while j >= 0 and data[j] > kunci:
            data[j + 1] = data[j]
            j = j - 1
        data[j + 1] = kunci
    return data
""")

add("binary_search", "algo", """
def binary_search(data, target):
    \"\"\"Cari target dalam list terurut, kembalikan indeks.\"\"\"
    kiri = 0
    kanan = len(data) - 1
    while kiri <= kanan:
        tengah = (kiri + kanan) // 2
        if data[tengah] == target:
            return tengah
        if data[tengah] < target:
            kiri = tengah + 1
        else:
            kanan = tengah - 1
    return -1
""", expect={R04})

add("linear_search", "algo", """
def linear_search(data, target):
    \"\"\"Cari target secara linear, kembalikan indeks pertama.\"\"\"
    for i in range(len(data)):
        if data[i] == target:
            return i
    return -1
""")

add("is_sorted", "algo", """
def is_sorted(data):
    \"\"\"Cek apakah list sudah terurut menaik.\"\"\"
    for i in range(len(data) - 1):
        if data[i] > data[i + 1]:
            return False
    return True
""")

add("hitung_inversi", "algo", """
def hitung_inversi(data):
    \"\"\"Hitung pasangan elemen yang tidak terurut.\"\"\"
    jumlah = 0
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] > data[j]:
                jumlah = jumlah + 1
    return jumlah
""")

add("quicksort", "algo", """
def quicksort(data):
    \"\"\"Urutkan list dengan quicksort (rekursif).\"\"\"
    if len(data) <= 1:
        return data
    pivot = data[len(data) // 2]
    kiri = [x for x in data if x < pivot]
    tengah = [x for x in data if x == pivot]
    kanan = [x for x in data if x > pivot]
    return quicksort(kiri) + tengah + quicksort(kanan)
""", expect={R04})

add("indeks_minimum", "algo", """
def indeks_minimum(data):
    \"\"\"Cari indeks nilai terkecil.\"\"\"
    if not data:
        return -1
    idx = 0
    for i in range(len(data)):
        if data[i] < data[idx]:
            idx = i
    return idx
""")

add("merge_dua_list", "algo", """
def merge(kiri, kanan):
    \"\"\"Gabung dua list terurut.\"\"\"
    hasil = []
    i = 0
    j = 0
    while i < len(kiri) and j < len(kanan):
        if kiri[i] <= kanan[j]:
            hasil.append(kiri[i])
            i = i + 1
        else:
            hasil.append(kanan[j])
            j = j + 1
    hasil.extend(kiri[i:])
    hasil.extend(kanan[j:])
    return hasil
""")

add("tambah_matriks", "algo", """
def tambah_matriks(a, b):
    \"\"\"Jumlahkan dua matriks berukuran sama.\"\"\"
    hasil = []
    for i in range(len(a)):
        baris = []
        for j in range(len(a[i])):
            baris.append(a[i][j] + b[i][j])
        hasil.append(baris)
    return hasil
""", expect={R02})

add("fizzbuzz", "algo", """
def fizzbuzz(n):
    \"\"\"Hasilkan deret FizzBuzz sampai n.\"\"\"
    hasil = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            hasil.append("FizzBuzz")
        elif i % 3 == 0:
            hasil.append("Fizz")
        elif i % 5 == 0:
            hasil.append("Buzz")
        else:
            hasil.append(str(i))
    return hasil
""", expect={R04})

# ============================================================
# 6) VALIDASI / INPUT
# ============================================================

add("is_tahun_kabisat", "validasi", """
def is_tahun_kabisat(tahun):
    \"\"\"Cek apakah tahun adalah tahun kabisat.\"\"\"
    if tahun % 4 != 0:
        return False
    if tahun % 100 != 0:
        return True
    return tahun % 400 == 0
""", expect={R04})

add("validasi_umur", "validasi", """
def validasi_umur(umur):
    \"\"\"Pastikan umur dalam rentang wajar.\"\"\"
    if umur < 0:
        return False
    if umur > 150:
        return False
    return True
""", expect={R04})

add("nilai_huruf", "validasi", """
def nilai_huruf(skor):
    \"\"\"Konversi skor angka menjadi nilai huruf.\"\"\"
    if skor >= 90:
        return "A"
    if skor >= 80:
        return "B"
    if skor >= 70:
        return "C"
    if skor >= 60:
        return "D"
    return "E"
""", expect={R04})

add("password_kuat", "validasi", """
def password_kuat(sandi):
    \"\"\"Cek apakah password cukup kuat.\"\"\"
    if len(sandi) < 8:
        return False
    ada_angka = any(c.isdigit() for c in sandi)
    ada_huruf = any(c.isalpha() for c in sandi)
    return ada_angka and ada_huruf
""", expect={R02, R04})

add("email_valid", "validasi", """
def email_valid(email):
    \"\"\"Validasi sederhana format email.\"\"\"
    if "@" not in email:
        return False
    if "." not in email:
        return False
    return True
""")

add("dalam_rentang", "validasi", """
def dalam_rentang(nilai, bawah, atas):
    \"\"\"Cek apakah nilai berada di [bawah, atas].\"\"\"
    return bawah <= nilai <= atas
""")

add("bisa_jadi_segitiga", "validasi", """
def bisa_jadi_segitiga(a, b, c):
    \"\"\"Cek apakah tiga sisi bisa membentuk segitiga.\"\"\"
    if a + b <= c:
        return False
    if a + c <= b:
        return False
    if b + c <= a:
        return False
    return True
""", expect={R02})

add("ke_int_aman", "validasi", """
def ke_int_aman(teks):
    \"\"\"Ubah teks ke int, kembalikan None bila gagal.\"\"\"
    try:
        return int(teks)
    except ValueError:
        return None
""")

add("username_valid", "validasi", """
def username_valid(nama):
    \"\"\"Username harus 3-20 karakter alfanumerik.\"\"\"
    if len(nama) < 3:
        return False
    if len(nama) > 20:
        return False
    return nama.isalnum()
""", expect={R04})

add("layak_diskon", "validasi", """
def layak_diskon(total_belanja, anggota):
    \"\"\"Tentukan apakah pelanggan layak diskon.\"\"\"
    if anggota and total_belanja > 100000:
        return True
    if total_belanja > 500000:
        return True
    return False
""", expect={R04})

add("nomor_hp_valid", "validasi", """
def nomor_hp_valid(nomor):
    \"\"\"Validasi nomor HP Indonesia sederhana.\"\"\"
    if not nomor.startswith("08"):
        return False
    if len(nomor) < 10:
        return False
    return nomor.isdigit()
""", expect={R04})

add("batasi_nilai", "validasi", """
def batasi_nilai(nilai):
    \"\"\"Pastikan nilai berada di rentang 0 sampai 100.\"\"\"
    if nilai < 0:
        return 0
    if nilai > 100:
        return 100
    return nilai
""", expect={R04})

add("jam_valid", "validasi", """
def jam_valid(jam, menit):
    \"\"\"Validasi jam dan menit.\"\"\"
    if jam < 0 or jam > 23:
        return False
    if menit < 0 or menit > 59:
        return False
    return True
""", expect={R04})

add("semua_positif", "validasi", """
def semua_positif(data):
    \"\"\"Cek apakah semua angka dalam list positif.\"\"\"
    for angka in data:
        if angka <= 0:
            return False
    return True
""")

# ============================================================
# 7) KEUANGAN / BISNIS
# ============================================================

add("hitung_diskon", "keuangan", """
def hitung_diskon(total_belanja):
    \"\"\"Hitung diskon berdasarkan total belanja.\"\"\"
    if total_belanja >= 500000:
        diskon = 0.1
    elif total_belanja >= 250000:
        diskon = 0.05
    else:
        diskon = 0
    return total_belanja * diskon
""", expect={R04})

add("hitung_pajak", "keuangan", """
def hitung_pajak(penghasilan):
    \"\"\"Hitung pajak penghasilan sederhana.\"\"\"
    if penghasilan <= 50000000:
        return penghasilan * 0.05
    return penghasilan * 0.15
""", expect={R04})

add("hitung_gaji_bersih", "keuangan", """
def hitung_gaji_bersih(gaji_pokok, tunjangan, potongan):
    \"\"\"Hitung gaji bersih.\"\"\"
    return gaji_pokok + tunjangan - potongan
""")

add("total_faktur", "keuangan", """
def total_faktur(harga_list):
    \"\"\"Jumlahkan semua harga dalam faktur.\"\"\"
    total = 0
    for harga in harga_list:
        total = total + harga
    return total
""")

add("hitung_tip", "keuangan", """
def hitung_tip(tagihan, persen):
    \"\"\"Hitung jumlah tip dari tagihan.\"\"\"
    return tagihan * persen / 100
""", expect={R04})

add("konversi_mata_uang", "keuangan", """
def konversi_mata_uang(jumlah, kurs):
    \"\"\"Konversi jumlah uang dengan kurs tertentu.\"\"\"
    return jumlah * kurs
""")

add("cicilan_bulanan", "keuangan", """
def cicilan_bulanan(pokok, bunga_tahun, bulan):
    \"\"\"Hitung cicilan bulanan (bunga flat).\"\"\"
    bunga = pokok * bunga_tahun / 100
    total = pokok + bunga
    return total / bulan
""", expect={R04})

add("margin_keuntungan", "keuangan", """
def margin_keuntungan(harga_jual, harga_beli):
    \"\"\"Hitung margin keuntungan dalam persen.\"\"\"
    if harga_jual == 0:
        return 0
    return (harga_jual - harga_beli) / harga_jual * 100
""", expect={R04})

add("hitung_cashback", "keuangan", """
def hitung_cashback(belanja):
    \"\"\"Cashback 10 persen maksimal 25 ribu.\"\"\"
    cashback = belanja * 0.1
    if cashback > 25000:
        return 25000
    return cashback
""", expect={R04})

add("sisa_anggaran", "keuangan", """
def sisa_anggaran(anggaran, pengeluaran_list):
    \"\"\"Hitung sisa anggaran setelah pengeluaran.\"\"\"
    total = sum(pengeluaran_list)
    return anggaran - total
""")

add("hitung_komisi", "keuangan", """
def hitung_komisi(penjualan):
    \"\"\"Hitung komisi penjualan bertingkat.\"\"\"
    if penjualan > 10000000:
        return penjualan * 0.1
    if penjualan > 5000000:
        return penjualan * 0.07
    return penjualan * 0.05
""", expect={R04})

add("denda_telat", "keuangan", """
def denda_telat(hari_telat, denda_per_hari):
    \"\"\"Hitung denda keterlambatan.\"\"\"
    if hari_telat <= 0:
        return 0
    return hari_telat * denda_per_hari
""")

add("hitung_roi", "keuangan", """
def hitung_roi(laba, modal):
    \"\"\"Hitung Return on Investment dalam persen.\"\"\"
    if modal == 0:
        return 0
    return laba / modal * 100
""", expect={R04})

add("rincian_cicilan", "keuangan", """
def rincian_cicilan(pokok, bulan):
    \"\"\"Cetak dan kembalikan cicilan per bulan.\"\"\"
    cicilan = pokok / bulan
    print("Cicilan per bulan:", cicilan)
    return cicilan
""", expect={R09})

# ============================================================
# 8) FILE / I/O & PENANGANAN ERROR
# ============================================================

add("baca_angka_bare", "errorhandling", """
def baca_angka(teks):
    \"\"\"Ubah teks jadi angka, kembalikan 0 bila gagal.\"\"\"
    try:
        return int(teks)
    except:
        return 0
""", expect={R01})

add("hapus_file", "errorhandling", """
import os


def hapus_file(path):
    \"\"\"Hapus file, abaikan bila tidak ada.\"\"\"
    try:
        os.remove(path)
    except:
        pass
""", expect={R01, R13})

add("bagi_aman", "errorhandling", """
def bagi_aman(a, b):
    \"\"\"Bagi a dengan b, kembalikan None bila pembagi nol.\"\"\"
    try:
        return a / b
    except ZeroDivisionError:
        return None
""", expect={R02})

add("ambil_config_pass", "errorhandling", """
def ambil_config(config, kunci):
    \"\"\"Ambil nilai config, abaikan bila key tidak ada.\"\"\"
    try:
        return config[kunci]
    except KeyError:
        pass
    return None
""", expect={R13})

add("hitung_kata_file", "errorhandling", """
def hitung_kata_file(isi):
    \"\"\"Hitung frekuensi kata dari isi file.\"\"\"
    frekuensi = {}
    for kata in isi.split():
        kata = kata.lower()
        frekuensi[kata] = frekuensi.get(kata, 0) + 1
    return frekuensi
""")

add("tulis_baris_with", "errorhandling", """
def tulis_baris(nama_file, baris_list):
    \"\"\"Tulis setiap baris ke file.\"\"\"
    with open(nama_file, "w") as f:
        for baris in baris_list:
            f.write(baris + "\\n")
""", expect={R02})  # R02 menandai 'f' (handle file) — idiomatik tapi diflag

add("baca_file_aman", "errorhandling", """
def baca_file(nama_file):
    \"\"\"Baca isi file, kembalikan string kosong bila gagal.\"\"\"
    try:
        with open(nama_file) as f:
            return f.read()
    except FileNotFoundError:
        return ""
""", expect={R02})  # R02 menandai 'f' (handle file)

add("parse_baris_csv", "errorhandling", """
def parse_baris_csv(baris):
    \"\"\"Pisahkan baris CSV menjadi list nilai.\"\"\"
    return baris.strip().split(",")
""")

add("hitung_valid_continue", "errorhandling", """
def hitung_valid(daftar_teks):
    \"\"\"Hitung berapa teks yang bisa jadi angka.\"\"\"
    jumlah = 0
    for teks in daftar_teks:
        try:
            int(teks)
            jumlah = jumlah + 1
        except ValueError:
            continue
    return jumlah
""")

add("coba_beberapa_kali", "errorhandling", """
def coba_beberapa_kali(fungsi, maks):
    \"\"\"Coba jalankan fungsi sampai berhasil.\"\"\"
    percobaan = 0
    while percobaan < maks:
        try:
            return fungsi()
        except:
            percobaan = percobaan + 1
    return None
""", expect={R01})

add("proses_aman_multi", "errorhandling", """
def proses_aman(data):
    \"\"\"Proses data dengan penanganan error spesifik.\"\"\"
    try:
        return int(data) * 2
    except ValueError:
        return 0
    except TypeError:
        return -1
""", expect={R04})

add("muat_pengaturan", "errorhandling", """
def muat_pengaturan(sumber):
    \"\"\"Muat pengaturan dengan nilai default.\"\"\"
    pengaturan = {}
    pengaturan["tema"] = sumber.get("tema", "terang")
    pengaturan["bahasa"] = sumber.get("bahasa", "id")
    return pengaturan
""")

add("buat_profil_json", "errorhandling", """
def buat_profil_json(nama, umur):
    \"\"\"Bangun representasi dict profil.\"\"\"
    return {
        "nama": nama,
        "umur": umur,
        "aktif": True,
    }
""")

add("catat_log", "errorhandling", """
def catat_log(pesan, level):
    \"\"\"Cetak pesan log berformat.\"\"\"
    baris = "[" + level + "] " + pesan
    print(baris)
""")

# ============================================================
# 9) GAME / SIMULASI
# ============================================================

add("menu_utama_loop", "game", """
def menu_utama():
    \"\"\"Tampilkan menu sampai pengguna keluar.\"\"\"
    while True:
        pilihan = input("Pilih menu: ")
        if pilihan == "keluar":
            print("Sampai jumpa")
            return
        print("Kamu memilih:", pilihan)
""")

add("loop_server_infinite", "game", """
def loop_server(antrian):
    \"\"\"Loop pemrosesan antrian tanpa henti.\"\"\"
    while True:
        antrian.proses_berikutnya()
""", expect={R14})

add("hitung_mundur_buggy", "game", """
def hitung_mundur(mulai):
    \"\"\"Hitung mundur dari 'mulai' (versi buggy tanpa henti).\"\"\"
    angka = mulai
    while True:
        print(angka)
        angka = angka + 1
""", expect={R14})

add("lempar_dadu", "game", """
import random


def lempar_dadu(jumlah):
    \"\"\"Lempar beberapa dadu, kembalikan total.\"\"\"
    total = 0
    for _ in range(jumlah):
        total = total + random.randint(1, 6)
    return total
""")

add("tebak_angka", "game", """
import random


def tebak_angka():
    \"\"\"Permainan tebak angka 1-100.\"\"\"
    rahasia = random.randint(1, 100)
    while True:
        tebakan = int(input("Tebak: "))
        if tebakan == rahasia:
            print("Benar!")
            break
        if tebakan < rahasia:
            print("Terlalu kecil")
        else:
            print("Terlalu besar")
""")

add("tentukan_pemenang_suit", "game", """
def tentukan_pemenang(pemain, lawan):
    \"\"\"Tentukan pemenang suit (gunting-batu-kertas).\"\"\"
    if pemain == lawan:
        return "Seri"
    menang = {"batu": "gunting", "gunting": "kertas", "kertas": "batu"}
    if menang[pemain] == lawan:
        return "Pemain"
    return "Lawan"
""")

add("catat_skor_papan", "game", """
def catat_skor(papan, nama, skor):
    \"\"\"Tambahkan skor pemain ke papan (list).\"\"\"
    papan.append((nama, skor))
""")

add("cek_pemenang_ttt", "game", """
def cek_pemenang(papan):
    \"\"\"Cek apakah ada baris yang menang di papan 3x3.\"\"\"
    for baris in papan:
        if baris[0] == baris[1] == baris[2] and baris[0] != "":
            return baris[0]
    return None
""", expect={R04})

add("statistik_koin", "game", """
import random


def statistik_koin(lemparan):
    \"\"\"Hitung jumlah kepala dari sejumlah lemparan koin.\"\"\"
    kepala = 0
    for _ in range(lemparan):
        if random.random() < 0.5:
            kepala = kepala + 1
    return kepala
""", expect={R04})

add("hitung_mundur_aman", "game", """
def hitung_mundur_aman(mulai):
    \"\"\"Hitung mundur dari 'mulai' sampai nol.\"\"\"
    angka = mulai
    while angka > 0:
        print(angka)
        angka = angka - 1
    print("Selesai")
""")

add("panjang_ular", "game", """
def panjang_ular(makanan_dimakan):
    \"\"\"Hitung panjang ular berdasarkan makanan.\"\"\"
    return 1 + makanan_dimakan
""")

add("histogram_dadu", "game", """
def histogram_dadu(lemparan):
    \"\"\"Hitung frekuensi tiap angka dadu.\"\"\"
    frekuensi = {}
    for nilai in lemparan:
        if nilai in frekuensi:
            frekuensi[nilai] = frekuensi[nilai] + 1
        else:
            frekuensi[nilai] = 1
    return frekuensi
""")

# ============================================================
# 10) TANGGAL/WAKTU & KONVERSI SATUAN
# ============================================================

add("detik_ke_jam", "konversi", """
def detik_ke_jam(total_detik):
    \"\"\"Konversi total detik menjadi jam, menit, detik.\"\"\"
    jam = total_detik // 3600
    sisa = total_detik % 3600
    menit = sisa // 60
    detik = sisa % 60
    return jam, menit, detik
""", expect={R04})

add("umur_dari_tahun", "konversi", """
def umur_dari_tahun(tahun_lahir, tahun_sekarang):
    \"\"\"Hitung umur berdasarkan tahun.\"\"\"
    return tahun_sekarang - tahun_lahir
""")

add("hari_dalam_bulan", "konversi", """
def hari_dalam_bulan(bulan, kabisat):
    \"\"\"Kembalikan jumlah hari dalam sebuah bulan.\"\"\"
    if bulan == 2:
        if kabisat:
            return 29
        return 28
    if bulan in (4, 6, 9, 11):
        return 30
    return 31
""", expect={R04})

add("nama_hari", "konversi", """
def nama_hari(indeks):
    \"\"\"Kembalikan nama hari dari indeks 0-6.\"\"\"
    hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    return hari[indeks]
""")

add("format_durasi", "konversi", """
def format_durasi(menit):
    \"\"\"Format durasi menit menjadi 'Xj Ym'.\"\"\"
    jam = menit // 60
    sisa = menit % 60
    return str(jam) + "j " + str(sisa) + "m"
""", expect={R04})

add("km_ke_mil", "konversi", """
def km_ke_mil(km):
    \"\"\"Konversi kilometer ke mil.\"\"\"
    return km * 0.621371
""", expect={R04})

add("kg_ke_pon", "konversi", """
def kg_ke_pon(kg):
    \"\"\"Konversi kilogram ke pon.\"\"\"
    return kg * 2.20462
""", expect={R04})

add("byte_ke_kb", "konversi", """
def byte_ke_kb(byte):
    \"\"\"Konversi byte ke kilobyte.\"\"\"
    return byte / 1024
""", expect={R04})

add("normalisasi_nilai", "konversi", """
def normalisasi(nilai, minimum, maksimum):
    \"\"\"Skala nilai ke rentang 0-1.\"\"\"
    if maksimum == minimum:
        return 0
    return (nilai - minimum) / (maksimum - minimum)
""")

add("interpolasi_linear", "konversi", """
def interpolasi(awal, akhir, t):
    \"\"\"Interpolasi linear antara awal dan akhir.\"\"\"
    return awal + (akhir - awal) * t
""", expect={R02})

add("celsius_ke_kelvin", "konversi", """
def celsius_ke_kelvin(celsius):
    \"\"\"Konversi Celsius ke Kelvin.\"\"\"
    return celsius + 273.15
""", expect={R04})

add("persen_ke_desimal", "konversi", """
def persen_ke_desimal(persen):
    \"\"\"Ubah persentase menjadi desimal.\"\"\"
    return persen / 100
""", expect={R04})

# ============================================================
# 11) REKURSI
# ============================================================

add("faktorial_rekursif", "rekursi", """
def faktorial(n):
    \"\"\"Faktorial n secara rekursif.\"\"\"
    if n <= 1:
        return 1
    return n * faktorial(n - 1)
""")

add("fibonacci_rekursif", "rekursi", """
def fibonacci(n):
    \"\"\"Bilangan Fibonacci ke-n secara rekursif.\"\"\"
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
""", expect={R04})

add("jumlah_sampai_n", "rekursi", """
def jumlah_sampai(n):
    \"\"\"Jumlahkan 1 sampai n secara rekursif.\"\"\"
    if n <= 0:
        return 0
    return n + jumlah_sampai(n - 1)
""")

add("pangkat_rec", "rekursi", """
def pangkat(basis, eksponen):
    \"\"\"Pangkat basis^eksponen secara rekursif.\"\"\"
    if eksponen == 0:
        return 1
    return basis * pangkat(basis, eksponen - 1)
""")

add("balik_string_rec", "rekursi", """
def balik_rekursif(teks):
    \"\"\"Balik string secara rekursif.\"\"\"
    if len(teks) <= 1:
        return teks
    return balik_rekursif(teks[1:]) + teks[0]
""")

add("hitung_mundur_rekursif", "rekursi", """
def hitung_mundur(n):
    \"\"\"Cetak hitung mundur secara rekursif.\"\"\"
    if n < 0:
        return
    print(n)
    hitung_mundur(n - 1)
""")

add("gcd_rekursif", "rekursi", """
def gcd(a, b):
    \"\"\"FPB secara rekursif (Euclid).\"\"\"
    if b == 0:
        return a
    return gcd(b, a % b)
""", expect={R02})

add("jumlah_digit_rec", "rekursi", """
def jumlah_digit(angka):
    \"\"\"Jumlahkan digit secara rekursif.\"\"\"
    if angka < 10:
        return angka
    return angka % 10 + jumlah_digit(angka // 10)
""", expect={R04})

# ============================================================
# 12) KODE PEMULA "BERANTAKAN" TAPI NYATA
#     (sengaja punya kebiasaan buruk yang umum ditemui)
# ============================================================

add("proses_pesanan_nodoc", "messy", """
def proses_pesanan(items):
    subtotal = 0
    for item in items:
        subtotal = subtotal + item["harga"]
    pajak = subtotal * 0.1
    total = subtotal + pajak
    return total
""", expect={R03, R04})

add("catat_transaksi_global", "messy", """
total_transaksi = 0


def catat_transaksi(jumlah):
    \"\"\"Catat transaksi ke akumulator global.\"\"\"
    global total_transaksi
    total_transaksi = total_transaksi + jumlah
""", expect={R12, R10})

add("keranjang_mutable_default", "messy", """
def tambah_ke_keranjang(barang, keranjang=[]):
    \"\"\"Tambahkan barang ke keranjang.\"\"\"
    keranjang.append(barang)
    return keranjang
""", expect={R08})

add("rapor_mutable_default", "messy", """
def catat_nilai(nama, nilai, rapor={}):
    \"\"\"Catat nilai siswa ke rapor.\"\"\"
    rapor[nama] = nilai
    return rapor
""", expect={R08})

add("buat_profil_banyak_param", "messy", """
def buat_profil(nama, umur, email, telepon, alamat, kota):
    \"\"\"Bangun dictionary profil pengguna.\"\"\"
    return {
        "nama": nama,
        "umur": umur,
        "email": email,
        "telepon": telepon,
        "alamat": alamat,
        "kota": kota,
    }
""", expect={R07})

add("setup_game_banyak_param", "messy", """
def setup_game(lebar, tinggi, fps, level, nyawa, skor_awal):
    \"\"\"Inisialisasi konfigurasi game.\"\"\"
    config = {}
    config["lebar"] = lebar
    config["tinggi"] = tinggi
    config["fps"] = fps
    config["level"] = level
    config["nyawa"] = nyawa
    config["skor"] = skor_awal
    return config
""", expect={R07})

add("validasi_transaksi_dalam", "messy", """
def validasi_transaksi(user, jumlah):
    \"\"\"Validasi transaksi berlapis.\"\"\"
    if user is not None:
        if user.aktif:
            if jumlah > 0:
                if user.saldo >= jumlah:
                    if jumlah < user.limit:
                        return True
    return False
""", expect={R05})

add("cari_di_grid_3d", "messy", """
def cari_di_grid(grid, target):
    \"\"\"Cari target dalam grid 3D bersarang.\"\"\"
    for lapis in grid:
        for baris in lapis:
            for sel in baris:
                if sel == target:
                    return True
    return False
""")  # 4 tingkat nesting → DI BAWAH ambang R05 (>4) → tidak diflag (temuan)

add("buat_invoice_panjang", "messy", """
def buat_invoice(pelanggan, items):
    \"\"\"Bangun invoice lengkap dari daftar item.\"\"\"
    subtotal = 0
    for item in items:
        subtotal = subtotal + item["harga"] * item["qty"]
    diskon = 0
    if subtotal > 1000000:
        diskon = subtotal * 0.1
    elif subtotal > 500000:
        diskon = subtotal * 0.05
    setelah_diskon = subtotal - diskon
    ppn = setelah_diskon * 0.11
    pajak_daerah = ppn * 0.1
    ongkir = 20000
    if setelah_diskon > 300000:
        ongkir = 0
    total = setelah_diskon + ppn + pajak_daerah + ongkir
    nama = pelanggan["nama"]
    alamat = pelanggan["alamat"]
    kota = pelanggan["kota"]
    pos = pelanggan["pos"]
    tanggal = pelanggan["tanggal"]
    nomor = pelanggan["nomor"]
    metode = pelanggan["metode"]
    catatan = pelanggan["catatan"]
    status = "lunas"
    return total
""", expect={R04, R06})

add("atur_tema_string_ulang", "messy", """
def atur_tema(mode):
    \"\"\"Tentukan warna teks dan latar sesuai mode.\"\"\"
    if mode == "gelap":
        teks = "putih"
        latar = "hitam"
    else:
        teks = "hitam"
        latar = "putih"
    return teks, latar
""", expect={R11})

add("hitung_ongkir_string_ulang", "messy", """
def hitung_ongkir(kota_asal, kota_tujuan):
    \"\"\"Hitung ongkir berdasarkan kota.\"\"\"
    if kota_asal == "Jakarta" and kota_tujuan == "Jakarta":
        return 10000
    if kota_asal == "Jakarta":
        return 25000
    return 50000
""", expect={R11, R04})

add("proses_data_duplikat", "messy", """
def proses_data_penjualan(data):
    \"\"\"Proses data penjualan.\"\"\"
    total = 0
    for nilai in data:
        total = total + nilai
    return total


def proses_data_pembelian(data):
    \"\"\"Proses data pembelian.\"\"\"
    total = 0
    for nilai in data:
        total = total + nilai
    return total
""", expect={R15})

add("kirim_pesan_duplikat", "messy", """
def kirim_email(penerima, pesan):
    koneksi = buka_koneksi()
    koneksi.kirim(penerima, pesan)
    koneksi.tutup()
    return True


def kirim_sms(penerima, pesan):
    koneksi = buka_koneksi()
    koneksi.kirim(penerima, pesan)
    koneksi.tutup()
    return True
""", expect={R15})

add("gabung_nama_nodoc", "messy", """
def gabung_nama(depan, tengah, belakang):
    hasil = depan
    hasil = hasil + " " + tengah
    hasil = hasil + " " + belakang
    hasil = hasil.strip()
    return hasil
""", expect={R03})

add("ambil_data_api", "messy", """
def ambil_data_api(url):
    respons = panggil(url)
    data = respons.json()
    hasil = data["items"]
    jumlah = len(hasil)
    try:
        rata = data["total"] / jumlah
    except:
        rata = 0
    return rata
""", expect={R03, R01})

add("hitung_satu_huruf", "messy", """
def hitung(p, q, r, s):
    a = p + q
    b = r + s
    c = a * b
    d = c - p
    return d
""", expect={R02, R03})

add("reset_status_global", "messy", """
aktif = 0
giliran = 0


def reset_status():
    global aktif
    global giliran
    aktif = 0
    giliran = 0
""", expect={R12, R10})

add("klasifikasi_suhu_dalam", "messy", """
def klasifikasi_suhu(suhu, kelembaban, angin, tekanan):
    \"\"\"Klasifikasi cuaca secara berlapis.\"\"\"
    if suhu > 30:
        if kelembaban > 70:
            if angin > 20:
                if tekanan < 1000:
                    return "badai"
    return "normal"
""", expect={R04})  # 4 if = 4 tingkat → di bawah ambang R05 (>4)

add("tambah_log_mutable_print", "messy", """
def tambah_log(pesan, riwayat=[]):
    \"\"\"Tambahkan pesan ke riwayat log.\"\"\"
    riwayat.append(pesan)
    print("log:", pesan)
    return riwayat
""", expect={R08, R09})

add("proses_semua_berantakan", "messy", """
def proses_semua(data):
    hasil = []
    for item in data:
        if item is not None:
            if item > 0:
                if item < 1000:
                    try:
                        nilai = 100 / item
                        hasil.append(nilai)
                    except:
                        hasil.append(0)
    return hasil
""", expect={R05, R01, R04})

# ============================================================
# 13) TAMBAHAN KODE BERSIH (idiomatik)
# ============================================================

add("celsius_list_comp", "misc", """
def semua_ke_fahrenheit(suhu_list):
    \"\"\"Konversi seluruh suhu Celsius ke Fahrenheit.\"\"\"
    return [c * 9 / 5 + 32 for c in suhu_list]
""", expect={R02, R04})

add("filter_dewasa", "misc", """
def ambil_dewasa(orang_list):
    \"\"\"Ambil orang berusia minimal 18 tahun.\"\"\"
    return [o for o in orang_list if o["umur"] >= 18]
""", expect={R02, R04})

add("gabung_dua_dict", "misc", """
def gabung_dict(a, b):
    \"\"\"Gabungkan dua dictionary.\"\"\"
    hasil = dict(a)
    hasil.update(b)
    return hasil
""", expect={R02})

add("hitung_total_keranjang", "misc", """
def total_harga(keranjang):
    \"\"\"Jumlahkan harga semua item di keranjang.\"\"\"
    return sum(item["harga"] for item in keranjang)
""")

add("urut_naik", "misc", """
def urut_naik(data):
    \"\"\"Kembalikan salinan list yang terurut menaik.\"\"\"
    return sorted(data)
""")

add("kapital_awal", "misc", """
def kapital_awal(teks):
    \"\"\"Kapitalkan huruf pertama tiap kata.\"\"\"
    return " ".join(kata.capitalize() for kata in teks.split())
""")

add("cek_kosong", "misc", """
def is_kosong(koleksi):
    \"\"\"True jika koleksi kosong.\"\"\"
    return len(koleksi) == 0
""")

add("ambil_unik_terurut", "misc", """
def unik_terurut(data):
    \"\"\"Kembalikan elemen unik yang terurut.\"\"\"
    return sorted(set(data))
""")

# ============================================================
# 14) SYNTAX ERROR (harus 422 + pesan baris)
# ============================================================

add("syn_def_tanpa_titik_dua", "syntax", """
def cek(x)
    return x
""", syntax_error=True)

add("syn_if_tanpa_titik_dua", "syntax", """
def f(x):
    if x > 0
        return x
    return 0
""", syntax_error=True)

add("syn_kurung_tidak_tutup", "syntax", """
def hitung(a, b):
    return (a + b
""", syntax_error=True)

add("syn_simbol_lebih_besar_sama", "syntax", """
def diskon(total):
    if total ≥ 1000:
        return total * 0.9
    return total
""", syntax_error=True)

add("syn_simbol_lebih_kecil_sama", "syntax", """
def naik(n):
    while n ≤ 10:
        n = n + 1
    return n
""", syntax_error=True)

add("syn_indentasi_hilang", "syntax", """
def f():
return 1
""", syntax_error=True)

add("syn_string_tak_tertutup", "syntax", """
pesan = "halo dunia
print(pesan)
""", syntax_error=True)

add("syn_kurung_param_rusak", "syntax", """
def f(:
    pass
""", syntax_error=True)

add("syn_print_python2", "syntax", """
print "halo dunia"
""", syntax_error=True)

add("syn_list_tanpa_koma", "syntax", """
angka = [1 2 3]
""", syntax_error=True)

add("syn_def_tanpa_nama", "syntax", """
def ():
    return 1
""", syntax_error=True)

add("syn_indent_tak_terduga", "syntax", """
def f():
    x = 1
      y = 2
    return x
""", syntax_error=True)

add("syn_ekspresi_tak_lengkap", "syntax", """
hasil = 5 +
print(hasil)
""", syntax_error=True)

add("syn_for_tanpa_titik_dua", "syntax", """
for i in range(10)
    print(i)
""", syntax_error=True)

# ==== INSERT BATCHES ABOVE ====
