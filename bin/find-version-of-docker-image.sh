#!/usr/bin/env bash
# A Utility that extracts the version from a Dockerfile's label
# Written by Sindre Nistad, snis@statoil.com
# Usage: ./find-version-of-docker-image.sh [folder in which the Docker file is]
declare version
declare -a arr

if [[ $# == 1 ]]; then
    CODE_DIR="$1"
else
    CODE_DIR="."
fi

version=$(grep version "${CODE_DIR}/Dockerfile" | tr  -d "\\\\" | tr "=" " " | tr "\"" " ")
trimmed_version=$(echo "${version}" | sed -e 's/^[ \t]*//')
arr=(${trimmed_version})
echo ${arr[2]}
