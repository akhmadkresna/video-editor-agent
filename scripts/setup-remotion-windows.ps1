# Windows house layout — run once after clone or when pnpm/Remotion breaks on G:
#   powershell -ExecutionPolicy Bypass -File scripts/setup-remotion-windows.ps1

$ErrorActionPreference = "Stop"

$Caches = "G:\AI\caches"
$PnpmStore = "$Caches\pnpm-store"
$RemotionScratch = "G:\AI\remotion-cache"

New-Item -ItemType Directory -Force -Path `
    $PnpmStore, `
    "$RemotionScratch\tmp", `
    "$RemotionScratch\binaries", `
    "$RemotionScratch\bundle-cache" | Out-Null

pnpm config set store-dir "G:/AI/caches/pnpm-store" --global

$env:REMOTION_SCRATCH_ROOT = $RemotionScratch
$env:AGENTIC_EDITOR_HOME = (Resolve-Path "$PSScriptRoot\..").Path

Write-Host "pnpm store -> $PnpmStore"
Write-Host "Remotion scratch -> $RemotionScratch"
Write-Host "AGENTIC_EDITOR_HOME -> $($env:AGENTIC_EDITOR_HOME)"

Push-Location $env:AGENTIC_EDITOR_HOME
try {
    pnpm install --store-dir $PnpmStore
    pnpm -r run build
    uv run ae doctor
} finally {
    Pop-Location
}

Write-Host "Done. Use: uv run ae compose <episode> --studio"
