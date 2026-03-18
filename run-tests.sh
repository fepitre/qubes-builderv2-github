#!/bin/bash
# Run tests locally exactly as GitLab CI would.
# Usage: ./run-tests.sh [PYTEST_TARGETS]
# Example: ./run-tests.sh "tests/test_action_bis.py -k test_action_"

set -e

CI_PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTEST_TARGETS="${*:-tests/}"

PYTEST_ARGS=(
    -vvv --showlocals --color=yes
    --tb=long
    --capture=no
    -rA
    -o truncation_limit_chars=0
    -o truncation_limit_lines=0
    -o junit_logging=all
    --junitxml="$CI_PROJECT_DIR/results/junit.xml"
)

# before_script
mkdir -p "$CI_PROJECT_DIR/results"

# script
# shellcheck disable=SC2086
TMPDIR=~ pytest-3 "${PYTEST_ARGS[@]}" $PYTEST_TARGETS
EXIT_CODE=$?

# after_script (always runs)
mkdir -p "$CI_PROJECT_DIR/results"
cp -r ~/pytest-of-"$USER"/pytest-current/github-current/*.log \
    "$CI_PROJECT_DIR/results"/ 2>/dev/null || true
cp -r ~/pytest-of-"$USER"/pytest-current/github-current/builder-github-logs \
    "$CI_PROJECT_DIR/results"/ 2>/dev/null || true

exit $EXIT_CODE
