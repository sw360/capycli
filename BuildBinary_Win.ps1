# --------------------------------------------------
# Build CaPyCLI binary for Windows using PyInstaller

# SPDX-FileCopyrightText: (c) 2026 Siemens
# SPDX-License-Identifier: MIT
# --------------------------------------------------

# Remove any existing build artifacts
Remove-Item -Path .\dist\capycli-win-x64.exe -Recurse -Force -ErrorAction Ignore
Remove-Item -Path .\dist\capycli.exe -Recurse -Force -ErrorAction Ignore

poetry run pyinstaller .\capycli.spec

Move-Item -Path .\dist\capycli.exe -Destination .\dist\capycli-win-x64.exe -Force

# --------------------------------------------------
# --------------------------------------------------
