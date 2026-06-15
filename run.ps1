# run.ps1 — Launcher AI Code Review Tutor
# - Jalankan server otomatis
# - Buka Chrome otomatis
# - Matikan server otomatis saat Chrome ditutup

$Host.UI.RawUI.WindowTitle = "AI Code Review Tutor"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Code Review Tutor" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Jalankan server uvicorn di background ──────────────────
Write-Host "Menjalankan server..." -ForegroundColor Yellow
$server = Start-Process -FilePath "uvicorn" `
    -ArgumentList "app:app", "--port", "8080" `
    -PassThru -WindowStyle Minimized

Write-Host "Menunggu server siap..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Cek apakah server benar-benar berjalan
$listening = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
    Write-Host "Gagal menjalankan server! Cek apakah port 8080 sudah dipakai." -ForegroundColor Red
    Read-Host "Tekan Enter untuk keluar"
    exit 1
}

Write-Host "Server berjalan di http://localhost:8080" -ForegroundColor Green
Write-Host ""

# ── 2. Hitung proses Chrome sebelum dibuka ────────────────────
$chromeBefore = @(Get-Process "chrome" -ErrorAction SilentlyContinue).Count

# ── 3. Buka Chrome ────────────────────────────────────────────
Write-Host "Membuka Chrome..." -ForegroundColor Yellow
$chromePath = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($chromePath) {
    Start-Process $chromePath "http://localhost:8080"
} else {
    # Fallback: buka dengan browser default
    Start-Process "http://localhost:8080"
    Write-Host "Chrome tidak ditemukan, membuka dengan browser default." -ForegroundColor DarkYellow
}

Start-Sleep -Seconds 2
$chromeAfter = @(Get-Process "chrome" -ErrorAction SilentlyContinue).Count

Write-Host ""
Write-Host "Tutup Chrome untuk menghentikan server secara otomatis." -ForegroundColor Green
Write-Host "Atau tekan Ctrl+C di window ini untuk berhenti manual." -ForegroundColor Gray
Write-Host ""

# ── 4. Monitor Chrome ─────────────────────────────────────────
if ($chromeAfter -gt $chromeBefore) {
    # Chrome baru dibuka — pantau sampai ditutup
    while ($true) {
        Start-Sleep -Seconds 2
        $chromeNow = @(Get-Process "chrome" -ErrorAction SilentlyContinue).Count
        if ($chromeNow -le $chromeBefore) { break }
    }
    Write-Host "Chrome ditutup. Menghentikan server..." -ForegroundColor Yellow
} else {
    # Chrome sudah berjalan sebelumnya — tunggu input manual
    Write-Host "Info: Chrome sudah berjalan sebelum launcher dijalankan." -ForegroundColor DarkYellow
    Write-Host "Tekan Enter untuk menghentikan server saat selesai..." -ForegroundColor Gray
    Read-Host
}

# ── 5. Matikan server ─────────────────────────────────────────
Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue

$portProc = (Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($portProc) {
    Stop-Process -Id $portProc -Force -ErrorAction SilentlyContinue
}

Write-Host "Server berhasil dihentikan." -ForegroundColor Green
Start-Sleep -Seconds 2
