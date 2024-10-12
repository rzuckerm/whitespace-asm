#!/bin/bash
PACKAGE="whitespace_asm"
META=".meta"
ARGS=()
if [ "$#" -lt 1 ]
then
    ARGS=( \
        -vvl \
        --color=yes \
        "--cov=${PACKAGE}" \
        --cov-branch \
        --cov-report term-missing \
        "--cov-report=html:${META}/html_cov/" \
        "--cov-report=xml:${META}/coverage.xml" \
    )
fi

mkdir -p .meta
poetry run pytest "${ARGS[@]}" "$@" test/
