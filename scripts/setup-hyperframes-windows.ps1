# Windows house layout — run once after clone or when pnpm/HyperFrames breaks on G:
#   powershell -ExecutionPolicy Bypass -File scripts/setup-hyperframes-windows.ps1

$ErrorActionPreference = "Stop"

$Caches = "G:\AI\caches"
$PnpmStore = "$Caches\pnpm-store"
$NpmCache = "$Caches\npm-cache"

# HyperFrames is invoked via `npx hyperframes@<pinned>` (see
# packages/hyperframes-kit/package.json), which auto-installs on first use and
# downloads Chrome Headless Shell for rendering. Both land under npm's own
# cache, so redirect that to G: alongside the pnpm store rather than the
# Remotion-specific scratch root the old pipeline used.
New-Item -ItemType Directory -Force -Path `
    $PnpmStore, `
    $NpmCache | Out-Null

pnpm config set store-dir "G:/AI/caches/pnpm-store" --global
npm config set cache "G:/AI/caches/npm-cache" --global

$env:npm_config_cache = $NpmCache
$env:AGENTIC_EDITOR_HOME = (Resolve-Path "$PSScriptRoot\..").Path

Write-Host "pnpm store -> $PnpmStore"
Write-Host "npm cache (hyperframes/npx/Chrome download) -> $NpmCache"
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
