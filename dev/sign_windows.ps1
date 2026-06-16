# Sign a Windows binary via Azure Trusted Signing (account "yhwhsigning").
#
#   pwsh -File dev/sign_windows.ps1                 # signs dist/YHWH.exe
#   pwsh -File dev/sign_windows.ps1 -File path.exe  # or dist/YHWH-0.1.0-windows-x64.exe (installer)
#
# One-time prereqs (already done on the N95):
#   Install-Module Az.Accounts, Az.Resources, TrustedSigning   # PSGallery, CurrentUser
#   The signer principal must hold the "Artifact Signing Certificate Profile Signer" role
#   (NOT "Trusted Signing …" — Microsoft renamed it) on the cert account, assigned BY OBJECT ID:
#     New-AzRoleAssignment -ObjectId <oid> -RoleDefinitionName 'Artifact Signing Certificate Profile Signer' -Scope <scope>
#   Owner is NOT sufficient; without the role you get 403 at sign time. (Already assigned + persists.)
# Full story + IDs: memory reference_windows_signing_azure.
param([string]$File = "$PSScriptRoot\..\dist\YHWH.exe")
$ErrorActionPreference = 'Stop'
Import-Module Az.Accounts
Import-Module TrustedSigning
if (-not (Get-AzContext)) {
    # Logs in to your default tenant/subscription (device code). The specific
    # tenant/subscription IDs are kept out of this public repo on purpose.
    Connect-AzAccount -UseDeviceAuthentication | Out-Null
}
Invoke-TrustedSigning `
    -Endpoint 'https://eus.codesigning.azure.net/' `
    -CodeSigningAccountName 'yhwhsigning' `
    -CertificateProfileName 'yhwh-public-trust' `
    -Files $File `
    -FileDigest SHA256 `
    -TimestampRfc3161 'http://timestamp.acs.microsoft.com' `
    -TimestampDigest SHA256
$sig = Get-AuthenticodeSignature $File
Write-Host ("Signature: " + $sig.Status + "  |  " + $sig.SignerCertificate.Subject)
if ($sig.Status -ne 'Valid') { exit 1 }
