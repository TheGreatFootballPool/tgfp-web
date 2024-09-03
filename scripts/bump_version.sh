#!/usr/bin/env bash
# usage: [major, minor, patch] "commit message"
cd "$(dirname "$0")" || exit

# move to the project root
cd ..
VERSION_FILE=config/version.env
if ! test -e ${VERSION_FILE}
then
  echo "You need to run this from the root directory.  File ${VERSION_FILE} is not found"
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
echo "New Version: $NEW_VERSION"
git add ${VERSION_FILE}
git commit -m "Updating version and pushing to production"
git push
git tag "v${NEW_VERSION}"
git push origin "v${NEW_VERSION}"