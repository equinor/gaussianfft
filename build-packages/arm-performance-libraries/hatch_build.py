from __future__ import annotations

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from gather_files import GatherArmPerformanceLibraries


class CustomBuildHook(BuildHookInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self, version, build_data):
        armpl = GatherArmPerformanceLibraries.ensure_arm_performance_libraries(
            app=self.app,
            version=self.metadata.hatch.version.cached,
            root=Path(self.root),
        )
        build_data["tag"] = "-".join(
            [
                "py3",
                "none",
                armpl.platform.replace("-", "_").replace(".", "_"),
            ]
        )
        # Files will only go to shared-data destinations, not package dir
        build_data["force_include_editable"] = {}
