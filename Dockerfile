# SPDX-FileCopyrightText: (c) 2018-2025 Siemens
# SPDX-License-Identifier: MIT

FROM python:3.12-slim

ARG VERSION

ARG MY_PATH=/opt/capycli
ARG MY_VENV=${MY_PATH}/venv

RUN mkdir -p "${MY_PATH}"
RUN python -m venv --without-pip "${MY_VENV}"
ENV VIRTUAL_ENV=${MY_VENV}
ENV PATH=${VIRTUAL_ENV}/bin:${PATH}

COPY ./dist ${MY_PATH}/dist
RUN pip --python "${MY_VENV}" \
   install --no-cache-dir --no-input --progress-bar=off \
   --verbose --debug \
   --prefix "${MY_VENV}" --require-virtualenv \
   --compile \
   "capycli==${VERSION}" --find-links "file://${MY_PATH}/dist"
RUN rm -rf ${MY_PATH}/dist

# reset entrypoint
ENTRYPOINT []
