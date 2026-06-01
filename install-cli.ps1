$ErrorActionPreference = "Stop"

$GithubUser = "harshjha4"
$GithubRepo = "easebuzz-cli"
# ⚠️ Ensure this exactly matches the name of the file you upload to GitHub Releases
$BinaryName = "easebuzz-cli-windows.exe"

Write-Host "Bootstrapping Easebuzz CLI (Standalone Binary) for Windows..." -ForegroundColor Cyan

# 1. Construct the GitHub Releases Download URL
$DownloadUrl = "https://github.com/$GithubUser/$GithubRepo/releases/latest/download/$BinaryName"

# 2. Define Local System Paths
$InstallDir = "$env:USERPROFILE\.easebuzz\bin"
$ExePath = "$InstallDir\easebuzz.exe"

Write-Host "Target installation directory: $InstallDir"

# 3. Create the Directory Structure
if (-Not (Test-Path $InstallDir)) {
    Write-Host "Creating installation directory..."
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
}

# 4. Download the Binary
Write-Host "Downloading ${BinaryName} from GitHub Releases..."
try {
    # This downloads the file and explicitly renames it to "easebuzz.exe"
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ExePath
} catch {
    Write-Host "Download failed. Make sure you have uploaded '${BinaryName}' to your GitHub Releases page." -ForegroundColor Red
    exit 1
}

# 5. Add to System PATH
Write-Host "Adding Easebuzz to your environment PATH..."
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")

# Check if the installation directory is already in the User's PATH
if ($UserPath -notmatch [regex]::Escape($InstallDir)) {
    $NewPath = "$UserPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
    Write-Host "IMPORTANT: Path updated! You must close and reopen this terminal for the changes to take effect." -ForegroundColor Yellow
} else {
    Write-Host "Directory is already in your PATH." -ForegroundColor Green
}

Write-Host "`Success! The Easebuzz CLI is installed." -ForegroundColor Green
Write-Host "Restart your PowerShell window, then type 'easebuzz --help' to get started." -ForegroundColor White