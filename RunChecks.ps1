# ------------------------------------------------
# Run quality checks

# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
# ------------------------------------------------

Write-Host "flake8 ..."
poetry run flake8

Write-Host "markdownlint ..."
npx -q markdownlint-cli *.md

Write-Host "isort ..."
isort .

# -----------------------------------
# -----------------------------------
