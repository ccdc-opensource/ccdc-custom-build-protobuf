#!/usr/bin/env python3
import shutil
import multiprocessing
from pathlib import Path
from ccdc.thirdparty.package import Package, AutoconfMixin, CMakeMixin


class ProtobufPackage(CMakeMixin, AutoconfMixin, Package):
    '''protobuf library and compiler'''
    name = 'protobuf'
    version = '3.11.4'

    def build(self):
        if not self.windows:
            super().build()
            return
        self.cleanup()
        self.fetch_source_archives()
        self.extract_source_archives()
        self.patch_sources()
        self.run_debug_configuration_script()
        self.run_debug_build_command()
        self.run_debug_install_command()
        self.run_configuration_script()
        self.run_build_command()
        self.run_install_command()
        self.verify()
        self.create_archive()

    @property
    def source_archives(self):
        return {
            f'{self.name}-all-{self.version}.tar.gz': f'https://github.com/protocolbuffers/protobuf/releases/download/v{self.version}/{self.name}-all-{self.version}.tar.gz'
        }

    @property
    def configuration_script(self):
        if not self.windows:
            return self.main_source_directory_path / 'configure'
        else:
            return Path(shutil.which('cmake'))

    @property
    def arguments_to_configuration_script(self):
        if not self.windows:
            return super().arguments_to_configuration_script + [
                '--disable-maintainer-mode',
                '--disable-static'
            ]
        return [
            '-G', self.visual_studio_generator_for_build,
            '-A', 'x64',
            '-DCMAKE_BUILD_TYPE=Release',
            f'-DCMAKE_INSTALL_PREFIX={self.install_directory}',
            '-Dprotobuf_BUILD_SHARED_LIBS=ON',
            f'{self.main_source_directory_path / "cmake"}'
        ]

    @property
    def arguments_to_debug_configuration_script(self):
        if not self.windows:
            raise Exception('debug is here for windows only')
        return [
            '-G', self.visual_studio_generator_for_build,
            '-A', 'x64',
            '-DCMAKE_BUILD_TYPE=Debug',
            f'-DCMAKE_INSTALL_PREFIX={self.install_directory}',
            '-Dprotobuf_BUILD_SHARED_LIBS=ON',
            f'{self.main_source_directory_path / "cmake"}'
        ]

    def run_debug_configuration_script(self):
        '''run the required commands to configure a package'''
        if not self.windows:
            raise Exception('debug is here for windows only')
        self.system(
            [str(self.configuration_script)] +
            self.arguments_to_debug_configuration_script,
            env=self.environment_for_configuration_script, cwd=self.build_directory_path)

    def run_build_command(self):
        if not self.windows:
            AutoconfMixin.run_build_command(self)
        else:
            CMakeMixin.run_build_command(self)

    def run_install_command(self):
        if not self.windows:
            AutoconfMixin.run_install_command(self)
        else:
            CMakeMixin.run_install_command(self)

    def run_debug_build_command(self):
        if not self.windows:
            raise Exception('debug is here for windows only')
        self.system([self.configuration_script, '--build', '.', '--config', 'Debug'],
                    env=self.environment_for_build_command, cwd=self.build_directory_path)

    def run_debug_install_command(self):
        if not self.windows:
            raise Exception('debug is here for windows only')
        self.system([self.configuration_script, '--install', '.', '--config', 'Debug'],
                    env=self.environment_for_build_command, cwd=self.build_directory_path)

def main():
    try:
        shutil.rmtree(ProtobufPackage().install_directory)
    except OSError:
        pass
    ProtobufPackage().build()


if __name__ == "__main__":
    main()
