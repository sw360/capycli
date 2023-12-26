# ------------------------------------------------
# Run quality checks

# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
# ------------------------------------------------

Write-Host "flake8 ..."
poetry run flake8

Write-Host "markdownlint ..."
# --disable MD041 forces NO error for the social image in Readme.md
npx -q markdownlint-cli *.md --disable MD041

Write-Host "isort ..."
poetry run isort .

Write-Host "mypy ..."
poetry run mypy .

Write-Host "Done."

# -----------------------------------
# -----------------------------------
