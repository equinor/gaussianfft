#!/bin/bash

# SPDX-FileCopyrightText: 2020 Intel Corporation
#
# SPDX-License-Identifier: MIT
# Copied from https://github.com/oneapi-src/oneapi-ci/blob/master/scripts/cache_exclude_windows.sh

#shellcheck disable=SC2010
LATEST_VERSION=$(ls -1 "C:\Program Files (x86)\Intel\oneAPI\compiler" | grep -v latest | sort | tail -1)

rm -rf "C:\Program Files (x86)\Intel\oneAPI\compiler\'$LATEST_VERSION'\windows\compiler\lib\ia32_win"
rm -rf "C:\Program Files (x86)\Intel\oneAPI\compiler\'$LATEST_VERSION'\windows\bin\intel64_ia32"
rm -rf "C:\Program Files (x86)\Intel\oneAPI\compiler\'$LATEST_VERSION'\windows\lib\emu"
rm -rf "C:\Program Files (x86)\Intel\oneAPI\compiler\'$LATEST_VERSION'\windows\lib\oclfpga"
rm -rf "C:\Program Files (x86)\Intel\oneAPI\compiler\'$LATEST_VERSION'\windows\lib\ocloc"
rm -rf "C:\Program Files (x86)\Intel\oneAPI\compiler\'$LATEST_VERSION'\windows\lib\x86"
