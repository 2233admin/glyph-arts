param(
    [string]$Repo = "2233admin/glyph-arts",
    [string]$VersionFile = "VERSION",
    [string]$Branch = "master",
    [string]$Tag = "",
    [switch]$AllowDirty
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

$inside = Run git @("rev-parse", "--is-inside-work-tree")
if (($inside | Select-Object -First 1) -ne "true") {
    Fail "Not inside a git worktree"
}

$currentBranchOutput = @(Run git @("branch", "--show-current"))
$currentBranch = ""
if ($currentBranchOutput.Count -gt 0 -and $null -ne $currentBranchOutput[0]) {
    $currentBranch = ([string]$currentBranchOutput[0]).Trim()
}
if ($currentBranch -and $currentBranch -ne $Branch) {
    Fail "Current branch is '$currentBranch', expected '$Branch'. Use a clean release worktree on $Branch."
}

$head = (Run git @("rev-parse", "HEAD") | Select-Object -First 1).Trim()
$remoteHead = (Run git @("rev-parse", "origin/$Branch") | Select-Object -First 1).Trim()
if ($head -ne $remoteHead) {
    Fail "HEAD ($head) does not match origin/$Branch ($remoteHead)"
}

if (-not $AllowDirty) {
    $status = Run git @("status", "--porcelain")
    if ($status) {
        Fail "Worktree is dirty. Commit, clean, or rerun with -AllowDirty for diagnostics only."
    }
}

$secretNames = Run gh @("secret", "list", "--repo", $Repo)
if (-not ($secretNames -match "^PYPI_API_TOKEN\s")) {
    Fail "Missing GitHub secret PYPI_API_TOKEN on $Repo"
}

$tagSha = ""
$tagOutput = & git rev-parse "$Tag^{}" 2>$null
if ($LASTEXITCODE -eq 0 -and $tagOutput) {
    $tagSha = ([string]($tagOutput | Select-Object -First 1)).Trim()
} else {
    Write-Host "Tag $Tag does not exist yet; it will need to be created at $head."
}

if ($tagSha -and $tagSha -ne $head) {
    Fail "Tag $Tag points to $tagSha, not HEAD $head. Move it only when ready to publish."
}

$packageName = "glyph-arts"
$pypiUrl = "https://pypi.org/pypi/$packageName/json"
try {
    $pypi = Invoke-RestMethod -Uri $pypiUrl
    if ($pypi.releases.PSObject.Properties.Name -contains $version) {
        Fail "PyPI already has $packageName $version. Do not republish the same version."
    }
    Write-Host "PyPI package exists, but $version is not published yet."
} catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404) {
        Write-Host "PyPI package $packageName does not exist yet; first publish is expected."
    } else {
        Fail "Could not query PyPI: $($_.Exception.Message)"
    }
}

Write-Host "Release preflight passed for $Repo $Tag at $head."
