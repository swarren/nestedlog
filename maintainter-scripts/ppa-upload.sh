#!/bin/bash

set -e

if [ -z "${DEBFULLNAME}" ]; then
    export DEBFULLNAME="Stephen Warren"
fi
if [ -z "${DEBEMAIL}" ]; then
    export DEBEMAIL="swarren@wwwdotorg.org"
fi

distros=()
distros+=(xenial)
distros+=(bionic)
distros+=(focal)

cd $(dirname "$0")/..

for distro in "${distros[@]}"; do
    git clean -fdx
    git reset --hard HEAD
    debchange -l "~${distro}" --distribution "${distro}" "PPA upload for ${distro}."
    pkgver=$(dpkg-parsechangelog --show-field Version)
    dpkg-buildpackage -S
    dput ppa:srwarren/nestedlog ../nestedlog_${pkgver}_source.changes
done

git clean -fdx
git reset --hard HEAD
