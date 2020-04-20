#!/usr/bin/env python3
import shutil
import multiprocessing
from ccdc.thirdparty.package import Package


class ProtobufPackage(Package):
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
        return shutil.which('cmake')

    @property
    def arguments_to_configuration_script(self):
        if not self.windows:
            return super().arguments_to_configuration_script + [
                '--disable-maintainer-mode',
                '--disable-static'
            ]
        return [
            '-G', 'Visual Studio 15 2017',
            '-A', 'x64',
            '-DCMAKE_BUILD_TYPE=Release',
            f'-DCMAKE_INSTALL_PREFIX={self.install_directory}',
            f'{self.main_source_directory_path / "cmake"}'
        ]


    def run_build_command(self):
        if not self.windows:
            super().run_build_command()
        else:
            self.system([self.configuration_script, '--build', '.', '--config', 'Release'],
                        env=self.environment_for_build_command, cwd=self.build_directory_path)


    def run_install_command(self):
        if not self.windows:
            super().run_install_command()
        else:
            self.system([self.configuration_script, '--install', '.'],
                    env=self.environment_for_build_command, cwd=self.build_directory_path)


def main():
    try:
        shutil.rmtree(ProtobufPackage().install_directory)
    except OSError:
        pass
    ProtobufPackage().build()


if __name__ == "__main__":
    main()
