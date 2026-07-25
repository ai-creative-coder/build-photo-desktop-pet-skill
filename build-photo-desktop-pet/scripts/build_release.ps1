param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [string]$ReleaseRoot = "",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$project = (Resolve-Path -LiteralPath $ProjectPath).Path
$configPath = Join-Path $project "src-tauri\tauri.conf.json"
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "Missing Tauri config: $configPath"
}
$config = Get-Content -LiteralPath $configPath -Encoding UTF8 -Raw | ConvertFrom-Json
$product = [string]$config.productName
$version = [string]$config.version
$specPath = Join-Path $project "project-spec.json"
if (-not (Test-Path -LiteralPath $specPath)) {
    throw "Missing project specification: $specPath"
}
$spec = Get-Content -LiteralPath $specPath -Encoding UTF8 -Raw | ConvertFrom-Json
if ($spec.custom_icon_ready -ne $true) {
    throw "Project icons still use the bundled generic chibi placeholder. Run generate_project_icons.py with the approved standing RGBA base before packaging."
}
foreach ($iconName in @("icon.png", "icon.ico")) {
    $iconPath = Join-Path $project ("src-tauri\icons\{0}" -f $iconName)
    if (-not (Test-Path -LiteralPath $iconPath)) {
        throw "Missing generated project icon: $iconPath"
    }
}
if (-not $ReleaseRoot) {
    $ReleaseRoot = Join-Path $project "output\releases"
}

& python (Join-Path $PSScriptRoot "validate_release_review.py") --project $project
if ($LASTEXITCODE -ne 0) {
    throw "Final visual review failed or is missing. Do not package this desktop pet."
}

Push-Location $project
try {
    if (-not $SkipInstall) {
        if (Test-Path -LiteralPath (Join-Path $project "package-lock.json")) {
            & npm ci
        } else {
            & npm install
        }
        if ($LASTEXITCODE -ne 0) { throw "npm dependency installation failed" }
    }
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw "frontend build failed" }
    & cargo test --manifest-path (Join-Path $project "src-tauri\Cargo.toml")
    if ($LASTEXITCODE -ne 0) { throw "Rust tests failed" }
    & npm run tauri build
    if ($LASTEXITCODE -ne 0) { throw "Tauri build failed" }
} finally {
    Pop-Location
}

$installer = Get-ChildItem -LiteralPath (Join-Path $project "src-tauri\target\release\bundle\nsis") -Filter "*.exe" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $installer) { throw "NSIS installer was not found" }

$releaseDir = Join-Path $ReleaseRoot ("{0}_{1}_Windows_x64" -f $product, $version)
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
$installerTarget = Join-Path $releaseDir ("{0}_{1}_Windows_x64_Setup.exe" -f $product, $version)
Copy-Item -LiteralPath $installer.FullName -Destination $installerTarget -Force

$docs = @(
    @{ Source = "DESKTOP_PET_USER_GUIDE.txt"; Target = "DESKTOP_PET_USER_GUIDE.txt" },
    @{ Source = "DESKTOP_PET_STATE_TRIGGER_GUIDE.md"; Target = "DESKTOP_PET_STATE_TRIGGER_GUIDE.md" }
)
foreach ($doc in $docs) {
    $source = Join-Path $project $doc.Source
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $releaseDir $doc.Target) -Force
    }
}

$hash = (Get-FileHash -LiteralPath $installerTarget -Algorithm SHA256).Hash
[pscustomobject]@{
    Product = $product
    Version = $version
    Installer = $installerTarget
    Bytes = (Get-Item -LiteralPath $installerTarget).Length
    SHA256 = $hash
} | Format-List
