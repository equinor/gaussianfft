#!/usr/bin/env python3

import sys
import os
from pathlib import Path

def find_mkl_config() -> Path | None:
    for root, dirs, files in os.walk(sys.prefix):
        for file in files:
            if file == "MKLConfig.cmake":
                return Path(root) / file
    return None


def run():
    mkl_config = find_mkl_config()
    if mkl_config is None:
        print("MKLConfig.cmake not found", file=sys.stderr)
        sys.exit(1)
    print(mkl_config)
    sys.exit(0)

if __name__ == '__main__':
    run()
