#!/usr/bin/env python3

import sys
import subprocess
import os
import stat
import shutil
import tempfile
import multiprocessing
from pathlib import Path
from distutils.version import StrictVersion


class Package(object):
    '''Base for anything installable'''
    name = None
    version = None
    _cached_sdkroot = None

    @property
    def macos(self):
        return sys.platform == 'darwin'

    @property
    def windows(self):
        return sys.platform == 'win32'

    @property
    def linux(self):
        return sys.platform.startswith('linux')

    @property
    def macos_sdkroot(self):
        if not self.macos:
            return None
        if not self._cached_sdkroot:
            self._cached_sdkroot = subprocess.check_output(
                ['xcrun', '--show-sdk-path'])[:-1].decode('utf8')
        return self._cached_sdkroot

    @property
    def macos_deployment_target(self):
        '''The minimum macos version the pagkage will work on'''
        return '10.12'

    def prepare_directories(self):
        if not self.toolbase.exists() and not self.windows:
            subprocess.check_output(['sudo', 'mkdir', '-p', '/opt/ccdc'])
            subprocess.check_output(['sudo', 'chown', f'{os.environ["USER"]}', '/opt/ccdc'])
        self.toolbase.mkdir(parents=True, exist_ok=True)
        self.source_downloads_base.mkdir(parents=True, exist_ok=True)
        self.source_extracted_base.mkdir(parents=True, exist_ok=True)
        self.source_builds_base.mkdir(parents=True, exist_ok=True)
        self.build_logs.mkdir(parents=True, exist_ok=True)

    @property
    def toolbase(self):
        '''Return the base directory where tools are installed'''
        if self.windows:
            return Path('D:\\x_mirror\\buildman\\tools')
        else:
            return Path('/opt/ccdc/third-party')

    @property
    def source_downloads_base(self):
        '''Return the directory where sources are downloaded'''
        if self.windows:
            return Path('D:\\tp\\downloads')
        else:
            return Path('/opt/ccdc/third-party-sources/downloads')

    @property
    def source_extracted_base(self):
        '''Return the base directory where sources are extracted'''
        if self.windows:
            return Path('D:\\tp\\extracted')
        else:
            return Path('/opt/ccdc/third-party-sources/extracted')

    @property
    def source_builds_base(self):
        '''Return the base directory where sources are built'''
        if self.windows:
            return Path('D:\\tp\\builds')
        else:
            return Path('/opt/ccdc/third-party-sources/builds')

    @property
    def build_logs(self):
        '''Return the directory where build logs are stored'''
        if self.windows:
            return Path('D:\\tp\\logs')
        else:
            return Path('/opt/ccdc/third-party-sources/logs')

    @property
    def install_directory(self):
        '''Return the canonical installation directory'''
        if 'BUILD_BUILDID' in os.environ:
            return self.toolbase / self.name / f'{self.name}-{self.version}-{os.environ["BUILD_BUILDID"]}'
        return self.toolbase / self.name / f'{self.name}-{self.version}'

    def create_archive(self):
        archive_name = self.install_directory.name + '.tar.gz'
        command = [
            'tar',
            '-zcf',
            f'{self.source_builds_base / archive_name}', # the tar filename
            f'{self.install_directory.relative_to(self.toolbase / self.name)}',
        ]
        try:
            self.system(command, cwd=self.toolbase / self.name) # keep the name + version directory in the archive, but not the package name directory
        except subprocess.CalledProcessError as e:
            if not self.windows:
                raise e
            command.insert(1,'--force-local') 
            self.system(command, cwd=self.toolbase / self.name) # keep the name + version directory in the archive, but not the package name directory

    @property
    def include_directories(self):
        '''Return the directories clients must add to their include path'''
        return [self.install_directory / 'include']

    @property
    def library_link_directories(self):
        '''Return the directories clients must add to their library link path'''
        return [self.install_directory / 'lib']

    @property
    def source_archives(self):
        '''Map of archive file/url to fetch'''
        return {}

    def fetch_source_archives(self):
        import urllib.request
        for filename, url in self.source_archives.items():
            if (self.source_downloads_base / filename).exists():
                print(
                    f'Skipping download of existing {self.source_downloads_base / filename}')
                continue
            print(f'Fetching {url} to {self.source_downloads_base / filename}')
            with urllib.request.urlopen(url) as response:
                with open(self.source_downloads_base / filename, 'wb') as final_file:
                    shutil.copyfileobj(response, final_file)

    def extract_source_archives(self):
        for source_archive_filename in self.source_archives.keys():
            self.extract_archive(self.source_downloads_base /
                                 source_archive_filename, self.source_extracted)

    def extract_archive(self, path, where):
        '''untar a file with any reasonable suffix'''
        print(f'Extracting {path} to {where}')
        if '.zip' in path.suffixes:
            self.system(['unzip', '-q', '-o', str(path)], cwd=where)
            return
        if '.bz2' in path.suffixes:
            flags = 'jxf'
        elif '.gz' in path.suffixes:
            flags = 'zxf'
        elif '.tgz' in path.suffixes:
            flags = 'zxf'
        elif '.xz' in path.suffixes:
            flags = 'xf'
        else:
            raise AttributeError(f"Can't extract {path}")

        if self.windows:
            flags = f'-{flags}'
            try:
                self.system(['tar', '--force-local', flags, str(path)], cwd=where)
            except subprocess.CalledProcessError:
                self.system(['tar', flags, str(path)], cwd=where)
        else:
            self.system(['tar', flags, str(path)], cwd=where)

    def patch_sources(self):
        '''Override to patch source code after extraction'''
        pass

    @property
    def source_downloads(self):
        p = self.source_downloads_base / self.name
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def source_extracted(self):
        p = self.source_extracted_base / self.name
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def main_source_directory_path(self):
        return self.source_extracted / f'{self.name}-{self.version}'

    @property
    def build_directory_path(self):
        p = self.source_builds_base / self.name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def cleanup(self):
        try:
            shutil.rmtree(self.source_extracted, ignore_errors=True)
            print(f'Cleaned up {self.source_extracted}')
        except OSError:
            pass
        try:
            shutil.rmtree(self.build_directory_path, ignore_errors=True)
            print(f'Cleaned up {self.build_directory_path}')
        except OSError:
            pass

    @property
    def configuration_script(self):
        return None

    @property
    def arguments_to_configuration_script(self):
        return [f'--prefix={self.install_directory}']

    @property
    def cxxflags(self):
        flags = [
            '-O2'
        ]
        if self.macos:
            flags.extend([
                '-arch', 'x86_64',
                '-isysroot', self.macos_sdkroot,
                f'-mmacosx-version-min={self.macos_deployment_target}',
            ])
        return flags

    @property
    def ldflags(self):
        flags = []
        if self.macos:
            flags.extend([
                '-arch', 'x86_64',
                '-isysroot', self.macos_sdkroot,
                f'-mmacosx-version-min={self.macos_deployment_target}',
            ])
        return flags

    @property
    def cflags(self):
        flags = [
            '-O2'
        ]
        if self.macos:
            flags.extend([
                '-arch', 'x86_64',
                '-isysroot', self.macos_sdkroot,
                f'-mmacosx-version-min={self.macos_deployment_target}',
            ])
        return flags

    @property
    def environment_for_configuration_script(self):
        env = dict(os.environ)
        if self.cflags:
            env['CFLAGS'] = ' '.join(self.cflags)
        if self.cxxflags:
            env['CXXFLAGS'] = ' '.join(self.cxxflags)
        if self.ldflags:
            env['LDFLAGS'] = ' '.join(self.ldflags)
        return env

    def run_configuration_script(self):
        '''run the required commands to configure a package'''
        if not self.configuration_script:
            print(f'Skipping configuration script for {self.name}')
            return
        st = os.stat(self.configuration_script)
        os.chmod(self.configuration_script, st.st_mode | stat.S_IEXEC)
        self.system(
            [str(self.configuration_script)] +
            self.arguments_to_configuration_script,
            env=self.environment_for_configuration_script, cwd=self.build_directory_path)

    @property
    def environment_for_build_command(self):
        return self.environment_for_configuration_script

    def run_build_command(self):
        '''run the required commands to build a package after configuration'''
        pass

    def run_install_command(self):
        '''run the required commands to install a package'''
        pass

    def logfile_path(self, task):
        '''Canonical log file for a particular task'''
        return self.build_logs / f'{self.name}-{self.version}-{task}.log'

    def system(self, command, cwd=None, env=None, append_log=False):
        '''execute command, logging in the appropriate logfile'''
        task = sys._getframe(1).f_code.co_name
        print(f'{self.name} {task}')
        if isinstance(command, str):
            command = [command]
        print(f'Running {command}')
        openmode = 'a' if append_log else 'w'
        with open(self.logfile_path(task), openmode) as f:
            output = ''
            p = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, env=env)
            while True:
                retcode = p.poll()
                l = p.stdout.readline().decode('utf-8')
                print(l.rstrip())
                output += l
                f.write(l)
                if retcode is not None:
                    break
            assert p.returncode is not None
            if p.returncode != 0:
                print(f'Failed process environment was {env}')
                raise subprocess.CalledProcessError(
                    returncode=p.returncode, cmd=command, output=output)

    def verify(self):
        '''Override this function to verify that the install has
        produced something functional.'''
        pass

    def build(self):
        self.cleanup()
        self.fetch_source_archives()
        self.extract_source_archives()
        self.patch_sources()
        self.run_configuration_script()
        self.run_build_command()
        self.run_install_command()
        self.verify()
        self.create_archive()

    def update_dylib_id(self, library_path, new_id):
        '''MacOS helper to change a library's identifier'''
        self.system(['install_name_tool', '-id', new_id, str(library_path)])

    def change_dylib_lookup(self, library_path, from_path, to_path):
        '''MacOS helper to change the path where libraries and executables look for other libraries'''
        self.system(['install_name_tool', '-change',
                     from_path, to_path, str(library_path)])

    def patch(self, fname, *subs):
        with open(fname) as read_file:
            txt = read_file.read()
        for (old, new) in subs:
            txt = txt.replace(old, new)
        with open(fname, 'w') as out:
            out.write(txt)


_pkg = Package()
_pkg.prepare_directories()
if _pkg.macos:
    assert os.path.exists(_pkg.macos_sdkroot)
_pkg = None


class GnuMakeMixin(object):
    '''Make based build'''

    def run_build_command(self):
        self.system(['make', f'-j{multiprocessing.cpu_count()}'],
                    env=self.environment_for_build_command, cwd=self.build_directory_path)


class MakeInstallMixin(object):
    '''Make install (rather than the default do nothing install)'''

    def run_install_command(self):
        self.system(['make', 'install'],
                    env=self.environment_for_build_command, cwd=self.build_directory_path)


class AutoconfMixin(GnuMakeMixin, MakeInstallMixin, object):
    '''Autoconf based configure script'''
    @property
    def configuration_script(self):
        return self.main_source_directory_path / 'configure'
