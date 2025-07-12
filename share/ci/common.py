import os
import subprocess as sub
import urllib.request
from shutil import which
import zipfile
import tarfile
import functools
import shutil
import multiprocessing
import platform
import re
import ast
import hashlib


print = functools.partial(print, flush=True)


def run(cmd, capture_output=False, silent=False):
    print('>> Running', cmd)
    if capture_output:
        result = sub.run(cmd, check=True, shell=True, universal_newlines=True,
                         stdout=sub.PIPE, stderr=sub.STDOUT)
        if not silent:
            print(result.stdout)
    else:
        if not silent:
            result = sub.run(cmd, check=True, shell=True)
        else:
            result = sub.run(cmd, check=True, shell=True,
                             stdout=sub.DEVNULL, stderr=sub.DEVNULL)
    return result


def download(url, out, force=False):
    print('>> Downloading', url, 'as', out)
    if not force and os.path.exists(out):
        print('>>', out, 'already exists')
        return
    out_path = os.path.dirname(out)
    if len(out_path) > 0:
        os.makedirs(out_path, exist_ok=True)
    urllib.request.urlretrieve(url, out)


def extract(src, dest):
    abs_path = os.path.abspath(src)
    print('>> Extracting', abs_path, 'to', dest)
    if len(dest) > 0:
        os.makedirs(dest, exist_ok=True)

    if which('cmake'):
        out = run('cmake -E tar t "{}"'.format(abs_path),
                  capture_output=True, silent=True)
        files = out.stdout.split('\n')
        already_exist = True
        for file in files:
            if not os.path.exists(os.path.join(dest, file)):
                already_exist = False
                break
        if already_exist:
            print('>> All files already exist')
            return
        sub.run('cmake -E tar xvf "{}"'.format(abs_path),
                check=True, shell=True, cwd=dest)
        return

    is_tar_smth = src.endswith('.tar', 0, src.rfind('.'))
    if which('7z'):
        sub.run('7z x "{}" -o"{}"'.format(abs_path, dest),
                check=True, shell=True, input=b'S\n')

        if is_tar_smth:
            inner_name = abs_path[:abs_path.rfind('.')]
            sub.run('7z x "{}" -o"{}"'.format(inner_name, dest),
                    check=True, shell=True, input=b'S\n')
        return

    if src.endswith('.tar') or is_tar_smth:
        path = abs_path if platform.system() != "Windows" else os.path.relpath(abs_path)
        if which('tar'):
            sub.run('tar xf "{}" --keep-newer-files -C "{}"'.format(path, dest),
                    check=True, shell=True)
            return

    raise RuntimeError('No archiver to extract {} file'.format(src))


def get_folder_files(path):
    result = []
    for root, _, files in os.walk(path):
        for file in files:
            result.append(os.path.join(root, file))
    return result


def get_archive_top_dir(path):
    """Return first top level folder name in given archive or raises RuntimeError"""
    with tarfile.open(path) as tar:
        first = tar.next()
        if not first is None:
            result = os.path.dirname(first.path)
            if len(result) == 0:
                result = first.path
            return result
    raise RuntimeError('Failed to open file or empty archive ' + path)


def archive(files, out):
    print('>> Archiving', files, 'into', out)
    if out.endswith('.zip'):
        arc = zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED)
        for f in files:
            arc.write(f)
        arc.close()
        return

    if out.endswith('.tar.gz'):
        arc = tarfile.open(out, 'w|gz')
        for f in files:
            arc.add(f)
        arc.close()
        return

    raise RuntimeError('No archiver to create {} file'.format(out))


def symlink(src, dest):
    print('>> Creating symlink', src, '=>', dest)
    norm_src = os.path.normcase(src)
    norm_dest = os.path.normcase(dest)
    
    # 检查源是否存在
    if not os.path.exists(norm_src):
        print('>> Error: Source does not exist:', norm_src)
        return False
    
    # 删除已存在的目标
    if os.path.lexists(norm_dest):
        try:
            if os.path.islink(norm_dest):
                os.unlink(norm_dest)
            elif os.path.isdir(norm_dest):
                shutil.rmtree(norm_dest)
            else:
                os.remove(norm_dest)
        except Exception as e:
            print('>> Warning: Failed to remove existing destination:', e)
    
    try:
        os.symlink(norm_src, norm_dest,
                   target_is_directory=os.path.isdir(norm_src))
        return True
    except OSError as e:
        print('>> Warning: Failed to create symlink, trying copy:', e)
        try:
            if os.path.isdir(norm_src):
                shutil.copytree(norm_src, norm_dest)
            else:
                shutil.copy2(norm_src, norm_dest)
            return True
        except Exception as copy_e:
            print('>> Error: Failed to copy as fallback:', copy_e)
            return False


def recreate_dir(path):
    shutil.rmtree(path, ignore_errors=True)
    os.mkdir(path)


def add_to_path(entry, prepend=True):
    path_separator = ';' if platform.system() == "Windows" else ':'
    os.environ['PATH'] = entry + path_separator + os.environ['PATH']


def get_msvc_env_cmd(bitness='64', msvc_version=''):
    """Return environment setup command for running msvc compiler for current platform"""
    if platform.system() != "Windows":
        return None

    # 尝试多个可能的Visual Studio路径
    possible_paths = [
        msvc_version + '/VC/Auxiliary/Build/vcvars{}.bat'.format(bitness),
        'C:/Program Files/Microsoft Visual Studio/2022/Enterprise/VC/Auxiliary/Build/vcvars{}.bat'.format(bitness),
        'C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvars{}.bat'.format(bitness),
        'C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars{}.bat'.format(bitness),
        'C:/Program Files (x86)/Microsoft Visual Studio/2019/Enterprise/VC/Auxiliary/Build/vcvars{}.bat'.format(bitness),
        'C:/Program Files (x86)/Microsoft Visual Studio/2019/Professional/VC/Auxiliary/Build/vcvars{}.bat'.format(bitness),
        'C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Auxiliary/Build/vcvars{}.bat'.format(bitness),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return '"' + path + '"'
    
    # 如果找不到，返回默认路径
    return '"' + possible_paths[0] + '"'


def get_cmake_arch_args(bitness='64'):
    if platform.system() != "Windows":
        return ''
    return '-A {}'.format('Win32' if bitness == '32' else 'x64')


def get_make_cmd():
    """Return `make` command for current platform"""
    if platform.system() == "Windows":
        # 检查是否有ninja可用
        if which('ninja'):
            return 'ninja'
        return 'nmake'
    else:
        # 检查是否有ninja可用
        if which('ninja'):
            return 'ninja'
        return 'make'


def set_make_threaded():
    """Adjust environment to run threaded make command"""
    if platform.system() == "Windows":
        os.environ['CL'] = '/MP'
    else:
        os.environ['MAKEFLAGS'] = '-j{}'.format(multiprocessing.cpu_count())


def is_inside_docker():
    """ Return True if running in a Docker container """
    with open('/proc/1/cgroup', 'rt') as f:
        return 'docker' in f.read()


def ensure_got_path(path):
    os.makedirs(path, exist_ok=True)


def apply_cmd_env(cmd):
    """Run cmd and apply its modified environment"""
    print('>> Applying env after', cmd)
    
    if platform.system() == "Windows":
        # Windows上使用更稳定的方法
        try:
            # 尝试运行vcvarsall.bat并获取环境
            result = sub.run(cmd + ' && set', shell=True, capture_output=True, text=True, encoding='cp437')
            if result.returncode == 0:
                # 解析环境变量
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if key and value:
                            os.environ[key.strip()] = value.strip()
                            print(f'>>> Set env {key.strip()}')
        except Exception as e:
            print(f'>> Warning: Failed to apply environment from {cmd}: {e}')
            # 如果失败，尝试使用vswhere找到Visual Studio
            try:
                result = sub.run('vswhere -latest -property installationPath', shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    vs_path = result.stdout.strip()
                    if vs_path:
                        vcvars_path = os.path.join(vs_path, 'VC', 'Auxiliary', 'Build', 'vcvars64.bat')
                        if os.path.exists(vcvars_path):
                            print(f'>> Using Visual Studio at: {vs_path}')
                            # 设置一些基本的环境变量
                            os.environ['VCINSTALLDIR'] = os.path.join(vs_path, 'VC')
                            os.environ['VSINSTALLDIR'] = vs_path
            except Exception as e2:
                print(f'>> Warning: Failed to find Visual Studio: {e2}')
    else:
        # Linux/macOS使用原来的方法
        separator = 'env follows'
        script = 'import os,sys;sys.stdout.buffer.write(str(dict(os.environ)).encode(\\\"utf-8\\\"))'
        env = sub.run('{} && echo "{}" && python -c "{}"'.format(cmd, separator, script),
                      shell=True, stdout=sub.PIPE, encoding='utf-8')

        stringed = env.stdout[env.stdout.index(separator) + len(separator) + 1:]
        parsed = ast.literal_eval(stringed)

        for key, value in parsed.items():
            if key in os.environ and os.environ[key] == value:
                continue
            if key in os.environ:
                print('>>> Changing env', key, '\nfrom\n',
                      os.environ[key], '\nto\n', value)
            os.environ[key] = value


def md5sum(path):
    if not os.path.exists(path):
        return ''
    md5 = hashlib.md5()
    with open(path, 'rb') as f:
        md5.update(f.read())
        return md5.hexdigest()
    return ''
