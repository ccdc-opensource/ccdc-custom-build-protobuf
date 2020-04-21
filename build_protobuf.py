#!/usr/bin/env python3
import shutil
import multiprocessing
from pathlib import Path
from ccdc.thirdparty.package import Package, AutoconfMixin, CMakeMixin


class ProtobufPackage(CMakeMixin, AutoconfMixin, Package):
    '''protobuf library and compiler'''
    name = 'protobuf'
    version = '3.11.4'

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
            '-G', f'Visual Studio {'16' if os.environ["BUILD_VS_VERSION"] == '2019' else '15'} {os.environ["BUILD_VS_VERSION"]}',
            '-A', 'x64',
            '-DCMAKE_BUILD_TYPE=Release',
            f'-DCMAKE_INSTALL_PREFIX={self.install_directory}',
            f'{self.main_source_directory_path / "cmake"}'
        ]

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


def main():
    try:
        shutil.rmtree(ProtobufPackage().install_directory)
    except OSError:
        pass
    ProtobufPackage().build()


if __name__ == "__main__":
    main()
