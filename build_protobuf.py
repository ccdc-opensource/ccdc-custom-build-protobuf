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
        return None

    @property
    def arguments_to_configuration_script(self):
        return super().arguments_to_configuration_script + [
            '--disable-maintainer-mode',
            '--disable-static'
        ]


    def run_build_command(self):
        self.system(['make', f'-j{multiprocessing.cpu_count()}'],
                    env=self.environment_for_build_command, cwd=self.build_directory_path)

    def run_install_command(self):
        self.system(['make', 'install'],
                    env=self.environment_for_build_command, cwd=self.build_directory_path)


def main():
    try:
        shutil.rmtree(ProtobufPackage().install_directory)
    except OSError:
        pass
    ProtobufPackage().build()


if __name__ == "__main__":
    main()
