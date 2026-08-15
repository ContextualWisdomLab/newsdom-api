ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823

FROM ${UV_IMAGE} AS uv-bin

FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:60e8ef87f2c0367254ff979a4dea61dad2684b001e3e666e2cc6fe992064dbbf

WORKDIR /src/newsdom-api
COPY --from=uv-bin /uv /uvx /usr/local/bin/
COPY . .
COPY .clusterfuzzlite/build.sh /src/build.sh
