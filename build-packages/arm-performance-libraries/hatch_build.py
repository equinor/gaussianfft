from __future__ import annotations

import os
import re
import sys
import tarfile
from collections.abc import Callable
from functools import wraps, cached_property
from http.client import HTTPResponse

import pydmg
from pathlib import Path
from typing import Literal, TYPE_CHECKING, TypedDict, cast
from urllib.request import urlopen
import subprocess

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from debx.ar import unpack_ar_archive

if TYPE_CHECKING:
    from hatchling.bridge.app import Application


TargetPlatform = Literal["macos", "linux_gcc"]


def get_platform():
    with open(Path(__file__).parent / ".platform.txt", "r") as f:
        return f.read().strip()


def get_target_platform() -> TargetPlatform:
    target_platform = os.environ.get("ARMPL_TARGET_PLATFORM")
    if target_platform is None or target_platform == "auto":
        mapping: dict[str, TargetPlatform] = {
            "darwin": "macos",
            "linux": "linux_gcc",
        }
        return mapping[sys.platform]
    if target_platform not in TargetPlatform.__args__:
        raise ValueError(
            f"Invalid target platform: {target_platform}. Must be one of {TargetPlatform.__args__}"
        )
    return cast(TargetPlatform, target_platform)


class CustomBuildHook(BuildHookInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        armpl = GatherArmPerformanceLibraries(
            app=self.app,
            armpl_version=self.metadata.hatch.version.cached,
            target_platform=get_target_platform(),
            root=Path(self.root),
            cache_dir=Path(self.root) / ".cache",
        )
        armpl.fetch()
        armpl.prepare()
        armpl.write_platform_file()

    def initialize(self, version, build_data):
        build_data["tag"] = "-".join(
            [
                "py3",
                "none",
                get_platform().replace("-", "_").replace(".", "_"),
            ]
        )
        # Files will only go to shared-data destinations, not package dir
        build_data["force_include_editable"] = {}


STATE = Literal["fetching", "fetched", "preparing", "prepared", "done", "failed"]


class StateMachineType(TypedDict):
    states: set[STATE | None]
    transitions: dict[STATE | None, set[STATE]]


STATE_MACHINE: StateMachineType = {
    "states": {"fetching", "fetched", "preparing", "prepared", "done", None},
    "transitions": {
        None: {"fetching"},
        "fetching": {"fetched"},
        "fetched": {"preparing"},
        "preparing": {"prepared"},
        "prepared": {"done"},
        "done": set(),
        "failed": {"fetching", "preparing"},
    },
}


def state_change(start: STATE, finished: STATE):
    if start not in STATE_MACHINE["states"]:
        raise ValueError(f"{start=} is not a valid state")
    if finished not in STATE_MACHINE["states"]:
        raise ValueError(f"{finished=} is not a valid state")
    if finished not in STATE_MACHINE["transitions"][start]:
        raise ValueError(f"{finished=} is not a valid transition for {start=}")

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self: GatherArmPerformanceLibraries, *args, **kwargs):
            state = self.state
            if start in STATE_MACHINE["transitions"][state] or state == start:
                self.state = start
                try:
                    func(self, *args, **kwargs)
                except Exception as e:
                    self.state = "failed"
                    raise e
                self.state = finished
            else:
                self.app.display_info(f"Skipping {func.__name__}; already done")

        return wrapper

    return decorator


class GatherArmPerformanceLibraries:
    @property
    def _state_file(self):
        return Path(self.cache_dir) / "build-state.txt"

    @property
    def state(self) -> STATE | None:
        if not self._state_file.exists():
            return None
        with open(self._state_file, "r") as f:
            # TODO: Validate
            return f.read().strip() or None

    @state.setter
    def state(self, value: STATE | None):
        if value is None:
            self._state_file.unlink(missing_ok=True)
            return
        with open(self._state_file, "w") as f:
            f.write(value)

    def __init__(
        self,
        app: Application,
        armpl_version: str,
        target_platform: TargetPlatform,
        root: Path,
        cache_dir: Path,
    ):
        self.app = app
        self.armpl_version = armpl_version
        self.root = root
        self.cache_dir = cache_dir
        self.target_platform = target_platform

    @property
    def cache_dir(self):
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self, value: Path):
        value.mkdir(exist_ok=True)
        self._cache_dir = value

    @property
    def target_platform(self):
        return self._target_platform

    @target_platform.setter
    def target_platform(self, value: Literal["macos", "linux_gcc"]):
        self._target_platform = value
        last_target_platform = self.cache_dir / "target-platform.txt"
        if last_target_platform.exists():
            with open(last_target_platform) as f:
                last_value = f.read().strip()
            if last_value != value:
                self.state = None
        else:
            self.state = None

        with open(self.cache_dir / "target-platform.txt", "w") as f:
            f.write(value)

    @state_change("prepared", "done")
    def write_platform_file(self):
        with open(self.root / ".platform.txt", "w") as f:
            f.write(self.platform)

    @property
    def platform(self):
        if self.target_platform == "macos":
            return "macosx-11.0-arm64"
        elif self.target_platform == "linux_gcc":
            return "linux-aarch64"
        else:
            raise NotImplementedError(f"Unsupported platform: {self.target_platform}")

    @state_change("preparing", "prepared")
    def prepare(self):
        for directory_glob in self.packaged_directories:
            directory = directory_glob.split("/")[0]
            if (target := self.root / directory).exists():
                for root, dirs, names in target.walk(top_down=False):
                    for name in names:
                        (root / name).unlink()
                    for name in dirs:
                        (root / name).rmdir()
                target.rmdir()

        for file in self._source_files:
            target = self.root / file
            target.parent.mkdir(parents=True, exist_ok=True)
            source = self.source_directory / file
            if source.is_file():
                source.copy(target)

    @cached_property
    def target_dir(self):
        return self.cache_dir / self.target_platform / self.armpl_version

    @cached_property
    def installation_target(self):
        return self.target_dir / "data"

    @cached_property
    def source_directory(self):
        if self.target_platform == "macos":
            options = list(
                self.installation_target.glob(f"armpl_{self.armpl_version}_flang-*")
            )
            if len(options) == 1:
                return options[0]
            else:
                raise FileNotFoundError(
                    f"Expected exactly one installation directory for ARM Performance libraries for {self.target_platform}, found {len(options)}"
                )

        elif self.target_platform == "linux_gcc":
            return (
                self.installation_target
                / "opt"
                / "arm"
                / f"armpl_{self.armpl_version}_gcc"
            )
        else:
            raise NotImplementedError(f"Unsupported platform: {self.target_platform}")

    @property
    def packaged_directories(self):
        return ["bin/*", "lib/**", "include/*", "license_terms/*"]

    @property
    def _source_files(self):
        if not self.source_directory.exists():
            self.fetch()
        source_files = []

        for glob in self.packaged_directories:
            for file in self.source_directory.glob(glob):
                if not file.is_symlink() and file.is_file():
                    source_files.append(file.relative_to(self.source_directory))

        return source_files

    @state_change("fetching", "fetched")
    def fetch(self):
        url = self._get_download_url()
        archive_path = self._download(url)
        installation_script = self._get_expected_installation_script()
        if not installation_script.exists():
            self._extract_archive(archive_path)
        self._extract_library_files(installation_script)

    def _get_download_url(self):
        if self.target_platform == "macos":
            return f"https://developer.arm.com/-/cdn-downloads/permalink/Arm-Performance-Libraries/Version_{self.armpl_version}/arm-performance-libraries_{self.armpl_version}_macOS.tgz"
        elif self.target_platform == "linux_gcc":
            return f"https://developer.arm.com/-/cdn-downloads/permalink/Arm-Performance-Libraries/Version_{self.armpl_version}/arm-performance-libraries_{self.armpl_version}_deb_gcc.tar"
        else:
            raise NotImplementedError(f"Unsupported platform: {self.target_platform}")

    def _download(self, url: str) -> Path:
        file_name = url.split("/")[-1]
        target_path = self.cache_dir / file_name
        if not target_path.exists():
            self.app.display_waiting(f"Fetching ARM Performance Libraries from {url}")
            with urlopen(url) as response, open(target_path, "wb") as f:
                f.write(cast(HTTPResponse, response).read())
        return target_path

    def _get_expected_installation_script(self):
        if self.target_platform == "macos":
            return self.target_dir / "install.sh"
        elif self.target_platform == "linux_gcc":
            return (
                self.target_dir
                / f"arm-performance-libraries_{self.armpl_version}_deb/arm-performance-libraries_{self.armpl_version}_deb.sh"
            )
        else:
            raise NotImplementedError(f"Unsupported platform: {self.target_platform}")

    def _extract_archive(
        self,
        archive_path: Path,
        ignore_unsupported: bool = False,
        target_dir: Path | None = None,
    ):
        if target_dir is None:
            target_dir = self.target_dir
        target_dir.mkdir(exist_ok=True, parents=True)
        if archive_path.suffix in [".tar", ".tgz"]:
            with tarfile.open(archive_path) as archive:
                archive.extractall(target_dir)
                for member in archive.getmembers():
                    if member.name.startswith("."):
                        continue
                    self._extract_archive(
                        target_dir / member.name, ignore_unsupported=True
                    )
        elif archive_path.suffix in [".dmg"]:
            for member in pydmg.list_apple_entries(archive_path):
                if not member["is_dir"] and member["path"].endswith(".sh"):
                    volume_path: str = member["path"]
                    target_path = target_dir / "install.sh"
                    self.app.display_waiting(
                        f"Extracting {volume_path} to {target_path}"
                    )
                    with open(target_path, "wb") as f:
                        f.write(pydmg.read_apple_file(archive_path, volume_path))
        elif archive_path.suffix in [".deb"]:
            with open(archive_path, "rb") as f:
                for file in unpack_ar_archive(f):
                    if file.name == "data.tar.gz/":
                        with tarfile.open(fileobj=file.fp) as archive:
                            archive.extractall(target_dir)
        elif not ignore_unsupported:
            raise NotImplementedError(
                f"Unsupported archive format: {archive_path.suffix}"
            )

    def _extract_library_files(self, installation_script: Path):
        if (
            not self.installation_target.exists()
            or len(list(self.installation_target.glob("*"))) == 0
        ):
            self.installation_target.mkdir(parents=True, exist_ok=True)
            if self.target_platform == "macos":
                command = subprocess.run(
                    [
                        "zsh",
                        str(installation_script),
                        "-y",
                        f"--install_dir={self.installation_target}",
                    ],
                    capture_output=True,
                )
            elif self.target_platform == "linux_gcc":
                if (_bash_version := bash_version()) < (5, 0, 0):
                    raise RuntimeError(
                        f"Bash version 5.0 or higher is required to install ARM Performance Libraries on Linux (got {_bash_version})"
                    )
                command = subprocess.run(
                    [
                        "bash",
                        str(installation_script),
                        "--accept",
                        "--save-packages-to",
                        str(self.installation_target),
                    ],
                    capture_output=True,
                )
            else:
                raise NotImplementedError(
                    f"Unsupported platform: {self.target_platform}"
                )
            self.app.display_info(command.stdout.decode())
            if command.stderr:
                self.app.display_waiting(command.stderr.decode())
            if command.returncode != 0:
                raise RuntimeError(
                    f"Installation script failed with exit code {command.returncode}"
                )

            # Post-install setup
            if self.target_platform == "linux_gcc":
                self._extract_archive(
                    self.installation_target / f"armpl_{self.armpl_version}_gcc.deb",
                    target_dir=self.installation_target,
                )


def bash_version():
    command = subprocess.run(["bash", "--version"], capture_output=True, check=True)
    match = re.search(
        r"GNU bash, version (?P<version>[0-9]+\.[0-9]+\.[0-9]+)",
        command.stdout.decode(),
    )
    if match:
        return tuple(int(part) for part in match.group("version").split("."))
    raise RuntimeError("Could not determine bash version")
