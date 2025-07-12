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
    qt_url = 'https://download.qt.io/official_releases/qt/{}/{}/single/qt-everywhere-src-{}.tar.xz'.format(
        qt_version, qt_version, qt_version)
    qt_archive = 'qt-everywhere-src-{}.tar.xz'.format(qt_version)
elif os_name == 'win64':
    qt_url = 'https://download.qt.io/official_releases/qt/{}/{}/single/qt-everywhere-src-{}.tar.xz'.format(
        qt_version, qt_version, qt_version)
    qt_archive = 'qt-everywhere-src-{}.tar.xz'.format(qt_version)
else:
    c.print('>> Unsupported OS: {}'.format(os_name))
    exit(1)

c.print('>> Downloading Qt from: {}'.format(qt_url))

try:
    c.download(qt_url, qt_archive)
    c.print('>> Qt downloaded successfully')
    
    # 解压Qt
    c.print('>> Extracting Qt...')
    c.extract(qt_archive, '.')
    
    # 查找解压后的目录
    qt_src_dir = None
    for item in os.listdir('.'):
        if item.startswith('qt-everywhere-src-'):
            qt_src_dir = item
            break
    
    if qt_src_dir and os.path.exists(qt_src_dir):
        c.print('>> Qt source directory found: {}'.format(qt_src_dir))
        
        # 创建Qt目录结构
        qt_install_dir = 'qt'
        os.makedirs(qt_install_dir, exist_ok=True)
        
        # 复制必要的文件
        import shutil
        if os.path.exists(os.path.join(qt_src_dir, 'qtbase')):
            shutil.copytree(os.path.join(qt_src_dir, 'qtbase'), os.path.join(qt_install_dir, 'qtbase'), dirs_exist_ok=True)
        if os.path.exists(os.path.join(qt_src_dir, 'qttools')):
            shutil.copytree(os.path.join(qt_src_dir, 'qttools'), os.path.join(qt_install_dir, 'qttools'), dirs_exist_ok=True)
        
        # 创建符号链接
        c.symlink(qt_install_dir, qt_dir)
        c.print('>> Qt setup completed')
    else:
        c.print('>> Error: Qt source directory not found')
        exit(1)
        
except Exception as e:
    c.print('>> Error downloading Qt: {}'.format(e))
    exit(1) 