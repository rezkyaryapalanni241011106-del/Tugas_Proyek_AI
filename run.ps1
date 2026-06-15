# run.ps1 — Launcher AI Code Review Tutor
# Menangani setup pertama kali secara otomatis:
#   1. Mencari Python di berbagai lokasi umum
#   2. Menginstall dependencies dari requirements.txt bila belum ada
#   3. Membuat file .env dari .env.example bila belum ada
#   4. Menjalankan server dan membuka browser

$Host.UI.RawUI.WindowTitle = "AI Code Review Tutor"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Code Review Tutor" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── LANGKAH 1: Cari Python ────────────────────────────────────
Write-Host "[1/4] Mencari Python..." -ForegroundColor Yellow

$python = $null
$candidates = @(
    "python",
    "python3",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:USERPROFILE\miniconda3\python.exe",
    "$env:USERPROFILE\anaconda3\python.exe",
    "$env:USERPROFILE\AppData\Local\miniconda3\python.exe",
    "C:\ProgramData\miniconda3\python.exe",
    "C:\ProgramData\anaconda3\python.exe"
)

foreach ($c in $candidates) {
    try {
        $ver = & "$c" --version 2>$null
        if ($LASTEXITCODE -eq 0 -and "$ver" -match "Python 3\.") {
            $python = $c
            Write-Host "    Ditemukan: $ver  ($c)" -ForegroundColor Green
            break
        }
    } catch { }
}

if (-not $python) {
    Write-Host ""
    Write-Host "ERROR: Python 3 tidak ditemukan di komputer ini." -ForegroundColor Red
    Write-Host "  > Install Python 3.10+ dari https://python.org" -ForegroundColor Red
    Write-Host "  > Centang 'Add Python to PATH' saat instalasi." -ForegroundColor Red
    Read-Host "Tekan Enter untuk keluar"
    exit 1
}

# ── LANGKAH 2: Install dependencies bila belum ada ────────────
Write-Host "[2/4] Memeriksa dependencies..." -ForegroundColor Yellow

& "$python" -c "import fastapi, uvicorn, groq, dotenv" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "    Menginstall dependencies (hanya perlu sekali)..." -ForegroundColor Yellow
    & "$python" -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: Gagal menginstall dependencies." -ForegroundColor Red
        Write-Host "  > Pastikan koneksi internet aktif, lalu jalankan ulang." -ForegroundColor Red
        Read-Host "Tekan Enter untuk keluar"
        exit 1
    }
    Write-Host "    Dependencies berhasil diinstall." -ForegroundColor Green
} else {
    Write-Host "    Semua dependencies sudah tersedia." -ForegroundColor Green
}

# ── LANGKAH 3: Siapkan file .env ──────────────────────────────
Write-Host "[3/4] Memeriksa konfigurasi..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "    File .env dibuat dari .env.example." -ForegroundColor Green
    Write-Host ""
    Write-Host "    +--------------------------------------------------+" -ForegroundColor Yellow
    Write-Host "    |  OPSIONAL: Untuk mengaktifkan penjelasan AI,     |" -ForegroundColor Yellow
    Write-Host "    |  buka file .env dan isi GROQ_API_KEY.            |" -ForegroundColor Yellow
    Write-Host "    |  Dapatkan key gratis di: https://console.groq.com|" -ForegroundColor Yellow
    Write-Host "    |  Aplikasi tetap berjalan tanpa key (mode umum).  |" -ForegroundColor Yellow
    Write-Host "    +--------------------------------------------------+" -ForegroundColor Yellow
    Write-Host ""
} else {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "GROQ_API_KEY=gsk_") {
        Write-Host "    GROQ_API_KEY terdeteksi - penjelasan AI aktif." -ForegroundColor Green
    } else {
        Write-Host "    GROQ_API_KEY belum diisi - mode fallback (tanpa AI)." -ForegroundColor DarkYellow
    }
}

# ── LANGKAH 4: Jalankan server ────────────────────────────────
Write-Host "[4/4] Menjalankan server di port 8080..." -ForegroundColor Yellow

$server = Start-Process -FilePath "$python" `
    -ArgumentList "-m", "uvicorn", "app:app", "--port", "8080" `
    -PassThru -WindowStyle Minimized

Write-Host "    Menunggu server siap..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

$listening = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
    Write-Host ""
    Write-Host "ERROR: Server gagal dijalankan!" -ForegroundColor Red
    Write-Host "  > Port 8080 mungkin sudah dipakai aplikasi lain." -ForegroundColor Red
    Write-Host "  > Tutup aplikasi lain yang memakai port 8080 lalu coba lagi." -ForegroundColor Red
    Read-Host "Tekan Enter untuk keluar"
    exit 1
}

Write-Host "    Server berjalan di http://localhost:8080" -ForegroundColor Green
Write-Host ""

# ── Buka browser ──────────────────────────────────────────────
$chromeBefore = @(Get-Process "chrome" -ErrorAction SilentlyContinue).Count

$chromePath = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($chromePath) {
    Start-Process $chromePath "http://localhost:8080"
} else {
    Start-Process "http://localhost:8080"
    Write-Host "    Chrome tidak ditemukan, membuka dengan browser default." -ForegroundColor DarkYellow
}

Start-Sleep -Seconds 2
$chromeAfter = @(Get-Process "chrome" -ErrorAction SilentlyContinue).Count

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Aplikasi berjalan di http://localhost:8080   " -ForegroundColor Cyan
Write-Host "  Tutup Chrome untuk menghentikan server.      " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── Monitor dan tunggu Chrome ditutup ─────────────────────────
if ($chromeAfter -gt $chromeBefore) {
    while ($true) {
        Start-Sleep -Seconds 2
        $chromeNow = @(Get-Process "chrome" -ErrorAction SilentlyContinue).Count
        if ($chromeNow -le $chromeBefore) { break }
    }
    Write-Host "Chrome ditutup. Menghentikan server..." -ForegroundColor Yellow
} else {
    Write-Host "Info: Chrome sudah berjalan sebelumnya." -ForegroundColor DarkYellow
    Write-Host "Tekan Enter untuk menghentikan server saat selesai..." -ForegroundColor Gray
    Read-Host
}

# ── Matikan server ────────────────────────────────────────────
Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue

$portProc = (Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($portProc) {
    Stop-Process -Id $portProc -Force -ErrorAction SilentlyContinue
}

Write-Host "Server berhasil dihentikan." -ForegroundColor Green
Start-Sleep -Seconds 2
