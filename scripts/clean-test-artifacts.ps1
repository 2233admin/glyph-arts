param(
    [switch]$RestoreTrackedTestOutputs
)

$ErrorActionPreference = "Stop"

function Remove-IfExists([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
        Write-Host "Removed $Path"
    }
}

function Is-Tracked([string]$Path) {
    & git ls-files --error-unmatch $Path *> $null
    return $LASTEXITCODE -eq 0
}

function Has-TrackedContent([string]$Path) {
    $tracked = & git ls-files -- $Path
    return [bool]$tracked
}

$repoRoot = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) {
    Write-Error "Not inside a git worktree"
    exit 1
}

Set-Location $repoRoot

$paths = @(
    ".pytest-tmp",
    ".pytest-tmp2",
    ".pytest-basetemp",
    ".pytest-p8-temp",
    ".tmp"
)

foreach ($path in $paths) {
    Remove-IfExists $path
}

if ((Test-Path -LiteralPath "uv.lock") -and -not (Is-Tracked "uv.lock")) {
    Remove-IfExists "uv.lock"
}

$generatedDirs = @()
if (Test-Path -LiteralPath "_temp") {
    $generatedDirs += Get-ChildItem -LiteralPath "_temp" -Directory -Filter "hyperframes-*"
}
if (Test-Path -LiteralPath "export_test_outputs\phase7a") {
    $generatedDirs += Get-ChildItem -LiteralPath "export_test_outputs\phase7a" -Directory
}

foreach ($dir in $generatedDirs) {
    $relativePath = Resolve-Path -LiteralPath $dir.FullName -Relative
    if (-not (Has-TrackedContent $relativePath)) {
        Remove-IfExists $dir.FullName
    }
}

if ($RestoreTrackedTestOutputs) {
    & git restore -- `
        export_test_outputs/no-color.html `
        export_test_outputs/out.ansi `
        export_test_outputs/out.txt `
        export_test_outputs/strips.html `
        export_test_outputs/wraps.html
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to restore tracked export test outputs"
        exit 1
    }
    Write-Host "Restored tracked export test outputs"
}

Write-Host "Test artifact cleanup complete."
