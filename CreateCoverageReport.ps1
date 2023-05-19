# ------------------------------------------------
# Run tests and create code coverage report

# SPDX-FileCopyrightText: (c) 2018-2023 Siemens
# SPDX-License-Identifier: MIT
# ------------------------------------------------

poetry run coverage run -m pytest
poetry run coverage report -m --omit "*/site-packages/*.py"
poetry run coverage html --omit "*/site-packages/*.py"


# -----------------------------------
# -----------------------------------
