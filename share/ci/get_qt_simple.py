import common as c
from config import qt_version, qt_dir, os_name
import os
import sys

c.print('>> Downloading Qt {} for {} (simplified method)'.format(qt_version, os_name))

# 确保当前目录存在
c.print('>> Current working directory: {}'.format(os.getcwd()))
c.print('>> Current directory contents:')
for item in os.listdir('.'):
    c.print('  - {}'.format(item))

# 使用更简单的Qt下载方法
if os_name == 'linux':
    # 使用Qt在线安装器的预编译包
    qt_url = 'https://download.qt.io/official_releases/qt/{}/linux_x64/qt-opensource-linux-x64-{}.run'.format(
        qt_version, qt_version)
    qt_archive = 'qt-opensource-linux-x64-{}.run'.format(qt_version)
elif os_name == 'win64':
    # 使用Qt在线安装器的预编译包
    qt_url = 'https://download.qt.io/official_releases/qt/{}/windows_x86/qt-opensource-windows-x86-{}.exe'.format(
        qt_version, qt_version)
    qt_archive = 'qt-opensource-windows-x86-{}.exe'.format(qt_version)
else:
    c.print('>> Unsupported OS: {}'.format(os_name))
    exit(1)

c.print('>> Downloading Qt from: {}'.format(qt_url))

try:
    # 尝试使用系统包管理器安装Qt
    if os_name == 'linux':
        c.print('>> Trying to install Qt via system package manager...')
        try:
            # 尝试使用apt安装Qt
            import subprocess
            result = subprocess.run(['sudo', 'apt-get', 'update'], capture_output=True, text=True)
            result = subprocess.run(['sudo', 'apt-get', 'install', '-y', 'qt5-default', 'qtbase5-dev', 'qttools5-dev'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                c.print('>> Qt installed via system package manager')
                
                # 创建Qt目录结构
                qt_install_dir = 'qt'
                os.makedirs(qt_install_dir, exist_ok=True)
                
                # 查找系统Qt安装
                qt_paths = ['/usr/lib/x86_64-linux-gnu/qt5', '/usr/lib/qt5', '/usr/share/qt5']
                qt_found = False
                for qt_path in qt_paths:
                    if os.path.exists(qt_path):
                        c.print('>> Found system Qt at: {}'.format(qt_path))
                        import shutil
                        shutil.copytree(qt_path, qt_install_dir, dirs_exist_ok=True)
                        qt_found = True
                        break
                
                if qt_found:
                    c.symlink(qt_install_dir, qt_dir)
                    c.print('>> Qt setup completed via system package manager')
                    exit(0)
                else:
                    c.print('>> System Qt not found in expected locations')
            else:
                c.print('>> System package manager installation failed')
        except Exception as e:
            c.print('>> System package manager failed: {}'.format(e))
    
    # 如果系统安装失败，尝试下载预编译包
    c.print('>> Trying to download Qt precompiled package...')
    c.download(qt_url, qt_archive)
    c.print('>> Qt downloaded successfully')
    
    # 对于Linux，尝试解压.run文件
    if os_name == 'linux':
        c.print('>> Extracting Qt installer...')
        # 给.run文件执行权限
        os.chmod(qt_archive, 0o755)
        
        # 尝试静默安装Qt
        try:
            import subprocess
            result = subprocess.run(['./{}'.format(qt_archive), '--script', 'qt_install.qs'], 
                                 capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                c.print('>> Qt installed successfully')
            else:
                c.print('>> Qt installer failed: {}'.format(result.stderr))
        except Exception as e:
            c.print('>> Qt installer error: {}'.format(e))
    
    # 创建基本的Qt目录结构
    qt_install_dir = 'qt'
    os.makedirs(qt_install_dir, exist_ok=True)
    
    # 创建符号链接
    c.symlink(qt_install_dir, qt_dir)
    c.print('>> Qt setup completed')
        
except Exception as e:
    c.print('>> Error downloading Qt: {}'.format(e))
    exit(1) 