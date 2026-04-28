param(
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-InstallPlan {
    $isWindowsHost = $env:OS -eq "Windows_NT"
    $isMacHost = (Get-Variable -Name IsMacOS -ErrorAction SilentlyContinue) -and $IsMacOS
    $isLinuxHost = (Get-Variable -Name IsLinux -ErrorAction SilentlyContinue) -and $IsLinux

    if ($isWindowsHost) {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            return [pscustomobject]@{
                Supported = $true
                Command = "winget install --id Microsoft.PowerShell --source winget"
                Recommendation = "Install PowerShell 7 with winget, then rerun the SocratexAI runtime check."
            }
        }
        return [pscustomobject]@{
            Supported = $true
            Command = "manual"
            Recommendation = "Install PowerShell 7 from Microsoft Store or GitHub releases, then rerun the SocratexAI runtime check."
        }
    }

    if ($isMacHost) {
        if (Get-Command brew -ErrorAction SilentlyContinue) {
            return [pscustomobject]@{
                Supported = $true
                Command = "brew install --cask powershell"
                Recommendation = "Install PowerShell 7 with Homebrew, then rerun the SocratexAI runtime check."
            }
        }
        return [pscustomobject]@{
            Supported = $true
            Command = "manual"
            Recommendation = "Install Homebrew or install PowerShell 7 from Microsoft documentation, then rerun the SocratexAI runtime check."
        }
    }

    if ($isLinuxHost) {
        if (Get-Command snap -ErrorAction SilentlyContinue) {
            return [pscustomobject]@{
                Supported = $true
                Command = "sudo snap install powershell --classic"
                Recommendation = "Install PowerShell 7 with snap, then rerun the SocratexAI runtime check."
            }
        }
        if (Get-Command apt -ErrorAction SilentlyContinue) {
            return [pscustomobject]@{
                Supported = $true
                Command = "see Microsoft PowerShell package repository instructions for apt-based Linux"
                Recommendation = "Configure the Microsoft package repository for your distribution, install PowerShell 7, then rerun the SocratexAI runtime check."
            }
        }
        return [pscustomobject]@{
            Supported = $true
            Command = "manual"
            Recommendation = "Install PowerShell 7 using the package manager supported by this Linux distribution, then rerun the SocratexAI runtime check."
        }
    }

    return [pscustomobject]@{
        Supported = $false
        Command = "unsupported"
        Recommendation = "This platform is not known to support SocratexAI PowerShell tooling. Use lite/no-tools mode, run the pipeline from a supported host, or port required scripts to the target shell before relying on automation."
    }
}

if (Get-Command pwsh -ErrorAction SilentlyContinue) {
    Write-Host "PowerShell 7 is already available."
    pwsh --version
    exit 0
}

$plan = Get-InstallPlan
Write-Host "PowerShell 7 is missing."
Write-Host "Supported: $($plan.Supported)"
Write-Host "Install command: $($plan.Command)"
Write-Host "Recommendation: $($plan.Recommendation)"

if (-not $Apply) {
    Write-Host "Dry run only. Rerun with -Apply after explicit user approval to install when a command is available."
    exit 0
}

if (-not $plan.Supported -or $plan.Command -in @("manual", "unsupported") -or $plan.Command -like "see *") {
    throw "Automatic PowerShell installation is not available. $($plan.Recommendation)"
}

if ($plan.Command -eq "winget install --id Microsoft.PowerShell --source winget") {
    winget install --id Microsoft.PowerShell --source winget
} elseif ($plan.Command -eq "brew install --cask powershell") {
    brew install --cask powershell
} elseif ($plan.Command -eq "sudo snap install powershell --classic") {
    sudo snap install powershell --classic
} else {
    throw "Unsupported install command: $($plan.Command)"
}

Write-Host "PowerShell installation command finished. Rerun tools/check_runtime.py to verify."
