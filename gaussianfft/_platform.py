import os
import sys
from pathlib import Path

if sys.platform == "win32":
    # Register the directory containing libiomp5md.dll if needed.
    # Priority: bundled DLL next to the package > oneAPI installation.
    _pkg_dir = Path(__file__).parent
    _bundled_dll = _pkg_dir.parent / "libiomp5md.dll"
    if _bundled_dll.is_file():
        os.add_dll_directory(str(_bundled_dll.parent.resolve()))
    else:
        _oneapi_root = os.environ.get("ONEAPI_ROOT")
        if _oneapi_root is None:
            _mklroot = os.environ.get("MKLROOT") or os.environ.get("MKL_ROOT")
            if _mklroot is not None:
                _oneapi_root = str(Path(_mklroot).parent.parent.resolve())
        if _oneapi_root is None:
            _default_paths = [
                Path(os.environ.get("ProgramFiles(x86)", "")) / "Intel" / "oneAPI",
                Path(os.environ.get("ProgramFiles", "")) / "Intel" / "oneAPI",
            ]
            for _path in _default_paths:
                if _path.is_dir():
                    _oneapi_root = str(_path)
                    break
        if _oneapi_root is not None:
            _intel_bin = Path(_oneapi_root) / "compiler" / "latest" / "bin"
            if _intel_bin.is_dir():
                os.add_dll_directory(str(_intel_bin.resolve()))
