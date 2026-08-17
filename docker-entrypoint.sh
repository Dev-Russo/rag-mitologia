#!/bin/sh
set -eu

CHROMA_PATH="${CHROMA_PATH:-/app/chroma_db}"
PDF_PATH="${PDF_PATH:-/app/data/ageoffableorstor00bulf_0.pdf}"
CHUNK_SIZE="${CHUNK_SIZE:-1000}"
CHUNK_OVERLAP="${CHUNK_OVERLAP:-150}"
INDEX_MARKER="${CHROMA_PATH}/.indexed-v1"

mkdir -p "${CHROMA_PATH}"

if [ "${SKIP_INGEST:-0}" != "1" ] && [ ! -f "${INDEX_MARKER}" ]; then
    echo "Preparando o corpus pela primeira vez..."
    python -m src.ingest "${PDF_PATH}" \
        --chunk-size "${CHUNK_SIZE}" \
        --chunk-overlap "${CHUNK_OVERLAP}" \
        --rebuild
    touch "${INDEX_MARKER}"
    echo "Corpus preparado."
fi

exec "$@"
