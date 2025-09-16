# PowerShell script to replace all author references
$oldAuthor = "程序那些事"
$newAuthor = "Wenrui Yu"

# Get all Python files in the MoneyPrinterPlus directory
$files = Get-ChildItem -Path "D:\MoneyPrinterPlus" -Recurse -Include "*.py" | Where-Object { $_.FullName -notlike "*__pycache__*" }

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match $oldAuthor) {
        Write-Host "Updating: $($file.FullName)"
        $content = $content -replace $oldAuthor, $newAuthor
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8
    }
}

# Also update markdown files
$mdFiles = Get-ChildItem -Path "D:\MoneyPrinterPlus" -Recurse -Include "*.md"

foreach ($file in $mdFiles) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match $oldAuthor) {
        Write-Host "Updating: $($file.FullName)"
        $content = $content -replace $oldAuthor, $newAuthor
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8
    }
}

Write-Host "Author replacement completed!"
