# ------------------------------------------------
# Run tests and create code coverage report

# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
# ------------------------------------------------

# 2022-07-15, T. Graf

poetry run coverage run -m pytest
poetry run coverage report -m --omit "*/site-packages/*.py",*/tests/*
poetry run coverage html --omit "*/site-packages/*.py",*/tests/*


# -----------------------------------
# -----------------------------------
