#!/usr/bin/env python3

import os
import sys
from pathlib import Path


def find_mkl_config(prefix_path: str) -> 'Path | None':
    for root, _, files in os.walk(prefix_path):
        for file in files:
            if file == 'MKLConfig.cmake':
                return Path(root) / file
    return None


def run():
    for prefix_path in sys.argv + [sys.prefix]:
        mkl_config = find_mkl_config(prefix_path)
        if mkl_config:
            print(mkl_config)
            sys.exit(0)
    sys.exit(1)


if __name__ == '__main__':
    run()
