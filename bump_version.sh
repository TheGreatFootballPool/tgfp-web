#!/usr/bin/env bash
# usage: [major, minor, patch] "commit message"
VERSION_FILE=version.env
if ! test -e ${VERSION_FILE}
then
  echo "You need to run this from the root directory.  File ${VERSION_FILE} is not found"
  exit 1
fi

if ! test $# -eq 2
then
  echo "This script needs to arguments [major, minor, patch] and \"commit message\""
  exit 1
fi

# shellcheck disable=SC1090
source ${VERSION_FILE}
echo "Previous Version: $MAJOR.$MINOR.$PATCH"
FOUND=false
case $1 in
  'major')
    (( MAJOR++ ))
    MINOR=0
    PATCH=0
    FOUND=true
    ;;
  'minor')
    (( MINOR++ ))
    PATCH=0
    FOUND=true
    ;;
  'patch')
    (( PATCH++ ))
    FOUND=true
    ;;
esac
{
  echo "MAJOR=$MAJOR"
  echo "MINOR=$MINOR"
  echo "PATCH=$PATCH"
} > ${VERSION_FILE}

if ! $FOUND
then
  echo "Needed major, minor, or patch as first parameter"
  exit 1
fi
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "$NEW_VERSION"
git add .
git commit -m "$2"
git push
git tag "v${NEW_VERSION}"
git push origin "v${NEW_VERSION}"