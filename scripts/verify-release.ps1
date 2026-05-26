param(
    [string]$Repo = "2233admin/glyph-arts",
    [string]$VersionFile = "VERSION",
    [string]$Tag = "",
    [switch]$SkipInstallSmoke
)

$ErrorActionPreference = "Stop"

function Fail($Message) {
    Write-Error $Message
    exit 1
}

function Run($Command, [string[]]$Arguments) {
    $output = & $Command @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        Fail "$Command $($Arguments -join ' ') failed: $output"
    }
    return $output
}

if (-not (Test-Path $VersionFile)) {
    Fail "Missing $VersionFile"
}

$version = (Get-Content $VersionFile -Raw).Trim()
if (-not $version) {
    Fail "$VersionFile is empty"
}

if (-not $Tag) {
    $Tag = "v$version"
}

$releaseList = Run gh @("release", "list", "--repo", $Repo, "--limit", "20")
$escapedTag = [regex]::Escape($Tag)
if (-not ($releaseList -match "^$escapedTag\s")) {
    Fail "GitHub release $Tag was not found in $Repo"
}

$runs = Run gh @("run", "list", "--repo", $Repo, "--workflow", "Publish to PyPI", "--branch", $Tag, "--limit", "5")
if (-not ($runs -match "^completed\s+success\s+")) {
    Fail "No successful Publish to PyPI workflow run found for $Tag"
}

$packageName = "glyph-arts"
$pypiUrl = "https://pypi.org/pypi/$packageName/json"
try {
    $pypi = Invoke-RestMethod -Uri $pypiUrl
} catch {
    Fail "Could not query PyPI: $($_.Exception.Message)"
}

if (-not ($pypi.releases.PSObject.Properties.Name -contains $version)) {
    Fail "PyPI does not list $packageName $version"
}

if (-not $SkipInstallSmoke) {
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("glyph-arts-verify-" + [System.Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        Run py @("-3", "-m", "venv", (Join-Path $tmp ".venv")) | Out-Null
        $python = Join-Path $tmp ".venv\Scripts\python.exe"
        Run $python @("-m", "pip", "install", "--upgrade", "pip") | Out-Null
        Run $python @("-m", "pip", "install", "--no-cache-dir", "$packageName==$version") | Out-Null
        Run $python @("-m", "cli_charts", "--help") | Out-Null
    } finally {
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Release verification passed for $packageName $version ($Tag)."
