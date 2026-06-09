# Get the git root directory and change to it
$gitRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to get git root directory"
    exit 1
}

Set-Location $gitRoot

# Remove the dist folder if it exists
if (Test-Path "./dist") {
    Remove-Item -Recurse -Force "./dist"
}

# Build the package
python -m build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed"
    exit 1
}

# Upload to PyPI
twine upload dist/*
