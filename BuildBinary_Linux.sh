# --------------------------------------------------
# Build CaPyCLI binary for Linux using PyInstaller

# SPDX-FileCopyrightText: (c) 2026 Siemens
# SPDX-License-Identifier: MIT
# --------------------------------------------------

# Remove any existing build artifacts
rm -f dist/capycli-linux-x64
rm -f dist/capycli

poetry run pyinstaller ./capycli.spec

mv dist/capycli dist/capycli-linux-x64

# --------------------------------------------------
# --------------------------------------------------
