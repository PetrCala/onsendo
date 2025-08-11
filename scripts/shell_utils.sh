#!/bin/bash

# Check if GREEN has already been defined
if [ -z "${GREEN+x}" ]; then
  declare -r GREEN=$'\e[1;32m'
fi

# Check if RED has already been defined
if [ -z "${RED+x}" ]; then
  declare -r RED=$'\e[1;31m'
fi

# Check if BLUE has already been defined
if [ -z "${BLUE+x}" ]; then
  declare -r BLUE=$'\e[1;34m'
fi

# Check if TITLE has already been defined
if [ -z "${TITLE+x}" ]; then
  declare -r TITLE=$'\e[1;4;34m'
fi

# Check if RESET has already been defined
if [ -z "${RESET+x}" ]; then
  declare -r RESET=$'\e[0m'
fi

function success {
  echo "🎉 $GREEN$1$RESET"
}

function error {
  echo "💥 $RED$1$RESET"
}

function info {
  echo "$BLUE$1$RESET"
}

function title {
  printf "\n%s%s%s\n" "$TITLE" "$1" "$RESET"
}

function assert_equal {
  if [[ "$1" != "$2" ]]; then
    error "Assertion failed: $1 is not equal to $2"
    return 1
  else
    success "Assertion passed: $1 is equal to $1"
  fi
}

# Usage: join_by_string <delimiter> ...strings
# example: join_by_string ' + ' 'string 1' 'string 2'
# example: join_by_string ',' "${ARRAY_OF_STRINGS[@]}"
function join_by_string {
  local separator="$1"
  shift
  local first="$1"
  shift
  printf "%s" "$first" "${@/#/$separator}"
}

# Usage: get_abs_path <path>
# Will make a path absolute, resolving any relative paths
# example: get_abs_path "./foo/bar"
get_abs_path() {
  local the_path=$1
  local -a path_elements
  IFS='/' read -ra path_elements <<<"$the_path"

  # If the path is already absolute, start with an empty string.
  # We'll prepend the / later when reconstructing the path.
  if [[ "$the_path" = /* ]]; then
    abs_path=""
  else
    abs_path="$(pwd)"
  fi

  # Handle each path element
  for element in "${path_elements[@]}"; do
    if [ "$element" = "." ] || [ -z "$element" ]; then
      continue
    elif [ "$element" = ".." ]; then
      # Remove the last element from abs_path
      abs_path=$(dirname "$abs_path")
    else
      # Append element to the absolute path
      abs_path="${abs_path}/${element}"
    fi
  done

  # Remove any trailing '/'
  while [[ $abs_path == */ ]]; do
    abs_path=${abs_path%/}
  done

  # Special case for root
  [ -z "$abs_path" ] && abs_path="/"

  # Special case to remove any starting '//' when the input path was absolute
  abs_path=${abs_path/#\/\//\/}

  echo "$abs_path"
}

function get_package_version {
  # Check if jq is installed
  if ! command -v jq &>/dev/null; then
    echo "jq is not installed. Please install jq to parse JSON files."
    return 1
  fi

  local package_json_path=$(get_abs_path "./package.json")

  if [ ! -f "$package_json_path" ]; then
    error "Package JSON file not found under this path: $package_json_path"
    error "Please make sure this script is placed in the ./scripts folder."
    return 1
  fi

  local version=$(jq -r '.version' "$package_json_path")
  echo "$version"
}

# Check whether an image tag exists. Return True if the image exists, False otherwise.
#
# Example usage:
#   my_image="localhost/artma/flask:v1"
#   if image_exists $my_image; then
#     echo "Image exists"
#   else
#     echo "Image does not exist"
#   fi
function image_exists {
  local tag="$1"
  if podman images --format "{{.Repository}}:{{.Tag}}" | grep -q "$tag"; then
    echo true
  else
    echo false
  fi
}

# Function to copy contents from one folder to another
#
# Example usage
#   copy_contents "$src" "$dest"
copy_contents() {
  local src_dir=$1
  local dest_dir=$2
  # Check if the source directory exists
  if [ ! -d "$src_dir" ]; then
    error "Source directory does not exist: $src_dir"
    return 1
  fi
  # Create the destination directory if it doesn't exist
  mkdir -p "$dest_dir"
  # Loop through all items in the source directory
  for item in "$src_dir"/*; do
    if [ -f "$item" ]; then
      # If the item is a file, copy it
      cp "$item" "$dest_dir"
    elif [ -d "$item" ]; then
      # If the item is a directory, call the function recursively
      local subdir_name=$(basename "$item")
      copy_contents "$item" "$dest_dir/$subdir_name"
    fi
  done
}

# Function to copy contents from the destination dir to the source dir.
# Copies only the files that exist in the source dir.
#
# Example usage
#   copy_contents_backwards "$from" "$to"
copy_contents_backwards() {
  local from_dir=$1
  local to_dir=$2
  # Check if the source directory exists
  if [ ! -d "$to_dir" ]; then
    error "Source directory does not exist: $to_dir"
    return 1
  fi
  # Loop through all items in the destination directory
  for to_item_path in "$to_dir"/*; do
    from_item_path="${to_item_path/$to_dir/$from_dir}" # Point to the new folder
    if [ ! -e "$from_item_path" ]; then
      # Item does not exist in the from folder
      continue
    elif [ -f "$to_item_path" ] && [ -f "$from_item_path" ]; then
      # If the item is a file in the source folder, copy its version in the current folder
      cp "$from_item_path" "$to_item_path"
    elif [ -d "$to_item_path" ] && [ -d "$from_item_path" ]; then
      # If the item is a directory and both folders exist, call the function recursively
      copy_contents_backwards "$from_item_path" "$to_item_path"
    else
      error "Could not find file $to_item_path. Skipping..."
    fi
  done
}

# Search for a parent folder within a search string. Return the full
#   path to the parent folder if found. Return an empty string otherwise.
#
# Usage:
#   parent_folder="$(search_for_parent_folder "folder_name" "path/to/folder_name/with/sub/paths")"
#   echo $parent_folder # "path/to/folder_name"
search_for_parent_folder() {
  local parent_folder_name=$1
  local search_string=$2

  parent_folder_search_string="$search_string"

  # Navigate up until one level above the parent folder name
  while [[ "$parent_folder_search_string" == *"$parent_folder_name"* ]]; do
    parent_folder_search_string="$(dirname $parent_folder_search_string)"
  done

  parent_folder="$parent_folder_search_string/$parent_folder_name"

  echo "$parent_folder"
}

# Check that a string is a valid semver
is_valid_semver() {
  local string=$1

  if [[ $string =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-((0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(\.(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*))?(\+([0-9a-zA-Z-]+(\.[0-9a-zA-Z-]+)*))?$ ]]; then
    echo true
  else
    echo false
  fi
}

function escape_slashes {
  sed 's/\//\\\//g'
}

#' Usage: change_line "TEXT_TO_BE_REPLACED" "NEW TEXT" yourFile
function change_line {
  local OLD_LINE_PATTERN=$1
  shift
  local NEW_LINE=$1
  shift
  local FILE=$1

  local NEW=$(echo "${NEW_LINE}" | escape_slashes)
  # FIX: No space after the option i.
  sed -i.bak '/'"${OLD_LINE_PATTERN}"'/s/.*/'"${NEW}"'/' "${FILE}"
  mv "${FILE}.bak" /tmp/
}

function load_static_variables {
  local script_name="$1"

  if [[ -f "$script_name" ]]; then
    source "$script_name"
  else
    error "File $script_name not found."
    return 1
  fi
}

# Get the current branch name
function get_current_branch {
  echo "$(git branch --show-current)"
}

function update_readme_badge {
  path=$1
  new_version=$2

  if [[ ! -f "$path" ]]; then
    error "The README file $path not found when trying to update the version badge."
    exit 1
  fi

  info "Updating the README file version badge"
  perl -i -p -e "s/badge\/version-(\d+\.\d+\.\d+)-/badge\/version-$new_version-/g" "$path"
}

# Validate that there are no unsaved changes in the checked out branch in the current folder. If there are, exit with an error message.
function validate_no_unsaved_changes {
  if [[ $(git status --porcelain) ]]; then
    error "There are unsaved changes in the folder. Please commit or stash your changes before running this script."
    exit 1
  fi
}

# Validate that all variables, defined in the input as an array of strings, exist in the environment. If not, exit with an error message.
function validate_env_variables {
  VARS=$1

  info "Checking environment variables..."
  for var in "${VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
      error "The environment variable $var is not set. Set it using 'export $var=<value>'..."
      exit 1
    fi
  done
}

# Check that folders exist, passed as arguments to the function. If any of the does not, exit with an error message.
function validate_folders_exist {
  should_fail=false
  for path in "$@"; do
    if [[ ! -d $path ]]; then
      error "The folder $path does not exist."
      should_fail=true
    fi
  done

  if [[ $should_fail == true ]]; then
    exit 1
  fi
}
