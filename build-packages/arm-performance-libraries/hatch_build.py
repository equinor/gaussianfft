import sysconfig

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        build_data['tag'] = '-'.join([
            'py3',
            'none',
            sysconfig.get_platform().replace('-', '_').replace('.', '_'),
        ])
        # Files will only go to shared-data destinations, not package dir
        build_data['force_include_editable'] = {}
