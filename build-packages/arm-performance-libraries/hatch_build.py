from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

def get_platform():
    with open(Path(__file__).parent / '.platform.txt', 'r') as f:
        return f.read().strip()

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        build_data['tag'] = '-'.join([
            'py3',
            'none',
            get_platform().replace('-', '_').replace('.', '_'),
        ])
        # Files will only go to shared-data destinations, not package dir
        build_data['force_include_editable'] = {}
