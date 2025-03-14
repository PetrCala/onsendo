#!/bin/bash

PROJECT_DIR_REL=$(dirname "${BASH_SOURCE[0]}")
source "$PROJECT_DIR_REL/scripts/shellUtils.sh"

PROJECT_ROOT="$(get_abs_path "$PROJECT_DIR_REL")"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
PACKAGE_DIR="scholar_wizard"

function run_lint {
  LINTRC_PATH="$PROJECT_ROOT/.pylintrc"
  LINT_PATH="$PACKAGE_DIR"
  TESTS_PATH="$PROJECT_ROOT/tests"
  pylint --recursive=y --rcfile="$LINTRC_PATH" "$LINT_PATH" "$TESTS_PATH" "$@"
}
function print_help {
  cat <<EOF
Usage: $0 <command> [args]

Available options:
  lint             - Lint the folder
  merge            - Merge the current branch into a specified one and push these changes to origin
  test             - Run unit tests
  test-all         - Run all tests
EOF
}

if [ $# -eq 0 ]; then
  print_help
  exit 1
fi

case ${1} in
lint)
  shift
  run_lint "$@"
  ;;
merge)
  shift
  source $SCRIPTS_DIR/mergeAndPush.sh "$@"
  ;;
test)
  pytest -q -m "not integration"
  ;;
test-all)
  pytest -q
  ;;
*)
  echo "Error: unknown command: $1"
  print_help
  exit 1
  ;;
esac
