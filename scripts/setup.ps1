$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$RequirementsFile = Join-Path $Root "requirements.txt"
$EnvFile = Join-Path $Root ".env"
$VenvDir = Join-Path $Root ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

$PythonVersion = "3.13.15"
$PythonSeries = "313"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message"
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARNING] $Message"
}

function Stop-Setup {
    param([string]$Message)
    Write-Host ""
    Write-Host "[ERROR] $Message"
    exit 1
}

function Test-CompatiblePython {
    param([string]$Executable, [string[]]$PrefixArgs = @())

    try {
        $check = & $Executable @PrefixArgs -c "import sys; print(sys.executable); print('%d.%d.%d' % sys.version_info[:3]); raise SystemExit(0 if sys.version_info >= (3, 10) else 2)" 2>$null
        if ($LASTEXITCODE -ne 0) {
            return $null
        }

        return @{
            Path = ($check | Select-Object -First 1)
            Version = ($check | Select-Object -Skip 1 -First 1)
        }
    }
    catch {
        return $null
    }
}

function Find-CompatiblePython {
    $pythonCommand = Get-Command "python.exe" -ErrorAction SilentlyContinue

    if ($pythonCommand -and $pythonCommand.Source -notlike "*\WindowsApps\*") {
        $result = Test-CompatiblePython -Executable $pythonCommand.Source
        if ($result) {
            return $result
        }
    }

    $pyCommand = Get-Command "py.exe" -ErrorAction SilentlyContinue

    if ($pyCommand) {
        $result = Test-CompatiblePython -Executable $pyCommand.Source -PrefixArgs @("-3")
        if ($result) {
            return $result
        }
    }

    $pythonRoot = Join-Path $env:LocalAppData "Programs\Python"

    if (Test-Path $pythonRoot) {
        $candidates = Get-ChildItem -Path $pythonRoot -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending

        foreach ($directory in $candidates) {
            $candidate = Join-Path $directory.FullName "python.exe"

            if (Test-Path $candidate) {
                $result = Test-CompatiblePython -Executable $candidate
                if ($result) {
                    return $result
                }
            }
        }
    }

    return $null
}

function Install-Python {
    Write-Step "Python 3.10+ was not found."
    Write-Host "The setup will install Python $PythonVersion from python.org."

    $arch = $env:PROCESSOR_ARCHITECTURE

    if ($env:PROCESSOR_ARCHITEW6432) {
        $arch = $env:PROCESSOR_ARCHITEW6432
    }

    switch ($arch.ToUpperInvariant()) {
        "AMD64" {
            $installerName = "python-$PythonVersion-amd64.exe"
        }
        "ARM64" {
            $installerName = "python-$PythonVersion-arm64.exe"
        }
        "X86" {
            $installerName = "python-$PythonVersion.exe"
        }
        default {
            Stop-Setup "Unsupported Windows architecture: $arch"
        }
    }

    $url = "https://www.python.org/ftp/python/$PythonVersion/$installerName"
    $installer = Join-Path $env:TEMP $installerName

    Write-Host "Downloading:"
    Write-Host "  $url"

    try {
        Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
    }
    catch {
        Stop-Setup "Python download failed. Check your internet connection."
    }

    Write-Step "Installing Python $PythonVersion"

    $process = Start-Process `
        -FilePath $installer `
        -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=1" `
        -Wait `
        -PassThru

    Remove-Item $installer -Force -ErrorAction SilentlyContinue

    if ($process.ExitCode -ne 0 -and $process.ExitCode -ne 3010) {
        Stop-Setup "Python installer failed with exit code $($process.ExitCode)."
    }

    $expectedPython = Join-Path $env:LocalAppData "Programs\Python\Python$PythonSeries\python.exe"

    if (Test-Path $expectedPython) {
        $result = Test-CompatiblePython -Executable $expectedPython
        if ($result) {
            Write-Ok "Python $($result.Version) installed."
            return $result
        }
    }

    $result = Find-CompatiblePython

    if ($result) {
        Write-Ok "Python $($result.Version) installed."
        return $result
    }

    Stop-Setup "Python was installed, but setup could not locate python.exe. Close this window and run setup.bat again."
}

function Get-EnvValue {
    param([string]$Name)

    if (-not (Test-Path $EnvFile)) {
        return ""
    }

    $pattern = "^\s*" + [regex]::Escape($Name) + "\s*=(.*)$"

    foreach ($line in Get-Content -LiteralPath $EnvFile) {
        if ($line -match $pattern) {
            return $Matches[1].Trim()
        }
    }

    return ""
}

function Test-TokenFormat {
    param([string]$Token)

    if ([string]::IsNullOrWhiteSpace($Token)) {
        return $false
    }

    if ($Token -eq "PASTE_YOUR_BOT_TOKEN_HERE") {
        return $false
    }

    return $Token -match '^\d+:[A-Za-z0-9_-]+$'
}

function Read-HiddenText {
    param([string]$Prompt)

    $secure = Read-Host $Prompt -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)

    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Test-TelegramToken {
    param([string]$Token)

    try {
        $result = Invoke-RestMethod `
            -Uri "https://api.telegram.org/bot$Token/getMe" `
            -Method Get `
            -TimeoutSec 10

        if ($result.ok -eq $true) {
            return @{
                Status = "Valid"
                Username = $result.result.username
            }
        }

        return @{
            Status = "Invalid"
            Username = ""
        }
    }
    catch {
        $message = $_.Exception.Message

        if ($message -match "401|Unauthorized|404|Not Found") {
            return @{
                Status = "Invalid"
                Username = ""
            }
        }

        return @{
            Status = "Unknown"
            Username = ""
        }
    }
}

function Get-ValidBotToken {
    $existing = Get-EnvValue -Name "BOT_TOKEN"

    if (Test-TokenFormat $existing) {
        Write-Step "Checking existing BOT_TOKEN"

        $check = Test-TelegramToken -Token $existing

        if ($check.Status -eq "Valid") {
            Write-Ok "Existing BOT_TOKEN is valid for @$($check.Username)."
            return $existing
        }

        if ($check.Status -eq "Unknown") {
            Write-Warn "Could not verify the existing token online. Keeping it because its format is valid."
            return $existing
        }

        Write-Warn "The existing BOT_TOKEN was rejected by Telegram."
    }
    else {
        Write-Step "BOT_TOKEN needs to be configured"
    }

    Write-Host "How to get it:"
    Write-Host "  1. Open Telegram and message @BotFather."
    Write-Host "  2. Use /newbot if you do not have a bot yet."
    Write-Host "  3. Copy the token BotFather gives you."
    Write-Host "  4. Do not share the token or commit it to Git."
    Write-Host ""
    Write-Host "Your input will be hidden while you paste the token."

    while ($true) {
        $token = (Read-HiddenText -Prompt "Paste BOT_TOKEN").Trim()

        if (-not (Test-TokenFormat $token)) {
            Write-Warn "That does not look like a Telegram Bot Token. Try again."
            continue
        }

        Write-Host "Verifying token with Telegram..."
        $check = Test-TelegramToken -Token $token

        if ($check.Status -eq "Valid") {
            Write-Ok "Token is valid for @$($check.Username)."
            return $token
        }

        if ($check.Status -eq "Invalid") {
            Write-Warn "Telegram rejected this token. Copy it again from @BotFather."
            continue
        }

        Write-Warn "Token could not be verified because Telegram was not reachable."
        $answer = Read-Host "Type USE to save it anyway, or press Enter to try another token"

        if ($answer.Trim().ToUpperInvariant() -eq "USE") {
            return $token
        }
    }
}

function Normalize-AdminIds {
    param([string]$Value)

    $normalized = ($Value -replace '\s', '')

    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return ""
    }

    if ($normalized -notmatch '^\d+(,\d+)*$') {
        return $null
    }

    return $normalized
}

function Get-AdminIds {
    $existing = Get-EnvValue -Name "ADMIN_IDS"
    $normalized = Normalize-AdminIds -Value $existing

    if ($null -ne $normalized -and $normalized -ne "") {
        Write-Ok "Existing ADMIN_IDS is valid: $normalized"
        return $normalized
    }

    if ($null -eq $normalized) {
        Write-Warn "Existing ADMIN_IDS is invalid."
    }

    Write-Step "Configure ADMIN_IDS"
    Write-Host "ADMIN_IDS contains the numeric Telegram user ID of each admin."
    Write-Host "Example:"
    Write-Host "  123456789"
    Write-Host "or for multiple admins:"
    Write-Host "  123456789,987654321"
    Write-Host ""
    Write-Host "If you do not know your Telegram ID yet:"
    Write-Host "  - Press Enter now."
    Write-Host "  - Finish setup and run run.bat."
    Write-Host "  - Send /start to the bot."
    Write-Host "  - Your Telegram ID will be printed in the terminal."
    Write-Host "  - Run setup.bat again and enter that ID."
    Write-Host ""

    while ($true) {
        $raw = Read-Host "ADMIN_IDS (or press Enter to set it later)"
        $normalized = Normalize-AdminIds -Value $raw

        if ($null -ne $normalized) {
            return $normalized
        }

        Write-Warn "Use only numeric IDs separated by commas."
    }
}

function Save-Environment {
    param(
        [string]$Token,
        [string]$AdminIds
    )

    $content = @(
        "BOT_TOKEN=$Token"
        "ADMIN_IDS=$AdminIds"
        ""
    ) -join [Environment]::NewLine

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($EnvFile, $content, $utf8NoBom)

    Write-Ok ".env was saved."
}

Write-Host "=========================================="
Write-Host " Telegram Shop Bot - Setup"
Write-Host "=========================================="

Write-Step "Checking Python"
$python = Find-CompatiblePython

if (-not $python) {
    $python = Install-Python
}
else {
    Write-Ok "Python $($python.Version) found at:"
    Write-Host "  $($python.Path)"
}

Write-Step "Preparing virtual environment"

if (Test-Path $VenvPython) {
    try {
        & $VenvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null

        if ($LASTEXITCODE -eq 0) {
            Write-Ok ".venv already exists."
        }
        else {
            throw "Invalid virtual environment"
        }
    }
    catch {
        Write-Warn "Existing .venv is broken or incompatible. Recreating it."
        Remove-Item $VenvDir -Recurse -Force
    }
}

if (-not (Test-Path $VenvPython)) {
    & $python.Path -m venv $VenvDir

    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPython)) {
        Stop-Setup "Could not create .venv."
    }

    Write-Ok ".venv created."
}

if (-not (Test-Path $RequirementsFile)) {
    Stop-Setup "requirements.txt is missing."
}

Write-Step "Installing Python packages"

& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Stop-Setup "pip upgrade failed."
}

& $VenvPython -m pip install -r $RequirementsFile
if ($LASTEXITCODE -ne 0) {
    Stop-Setup "Package installation failed. Check your internet connection."
}

Write-Ok "Python packages installed."

Write-Step "Checking bot configuration"

$token = Get-ValidBotToken
$adminIds = Get-AdminIds

Save-Environment -Token $token -AdminIds $adminIds

Write-Host ""
Write-Host "=========================================="
Write-Host " Setup finished successfully"
Write-Host "=========================================="
Write-Host ""
Write-Host "Next:"
Write-Host "  1. Double-click run.bat."
Write-Host "  2. Open your bot in Telegram."
Write-Host "  3. Send /start."
Write-Host "  4. Confirm that the main menu appears."
Write-Host ""

if ([string]::IsNullOrWhiteSpace($adminIds)) {
    Write-Warn "ADMIN_IDS is still empty."
    Write-Host "After /start, copy the Telegram ID printed in the terminal."
    Write-Host "Then run setup.bat again and enter that ID."
}
else {
    Write-Ok "ADMIN_IDS is configured."
}

exit 0
