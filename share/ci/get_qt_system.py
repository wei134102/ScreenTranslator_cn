import common as c
from config import qt_dir, os_name
import os
import subprocess

c.print('>> Installing Qt via system package manager for {}'.format(os_name))

# 确保当前目录存在
c.print('>> Current working directory: {}'.format(os.getcwd()))

if os_name == 'linux':
    c.print('>> Installing Qt5 via apt...')
    try:
        # 更新包列表
        result = subprocess.run(['sudo', 'apt-get', 'update'], 
                             capture_output=True, text=True, check=True)
        c.print('>> Package list updated')
        
        # 安装Qt5开发包
        qt_packages = [
            'qt5-default',
            'qtbase5-dev',
            'qttools5-dev',
            'qtwebengine5-dev',
            'libqt5webkit5-dev',
            'qt5-qmake',
            'qtchooser'
        ]
        
        for package in qt_packages:
            c.print('>> Installing {}...'.format(package))
            result = subprocess.run(['sudo', 'apt-get', 'install', '-y', package], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                c.print('>> {} installed successfully'.format(package))
            else:
                c.print('>> Warning: {} installation failed: {}'.format(package, result.stderr))
        
        # 创建Qt目录结构
        qt_install_dir = 'qt'
        os.makedirs(qt_install_dir, exist_ok=True)
        os.makedirs(os.path.join(qt_install_dir, 'bin'), exist_ok=True)
        
        # 查找系统Qt安装
        qt_paths = [
            '/usr/lib/x86_64-linux-gnu/qt5',
            '/usr/lib/qt5',
            '/usr/share/qt5',
            '/usr/lib/x86_64-linux-gnu/qt5/bin',
            '/usr/bin'
        ]
        
        qt_found = False
        for qt_path in qt_paths:
            if os.path.exists(qt_path):
                c.print('>> Found Qt at: {}'.format(qt_path))
                # 创建符号链接到我们的qt目录
                if qt_path.endswith('/bin'):
                    # 如果是bin目录，复制qmake等工具
                    import shutil
                    for file in os.listdir(qt_path):
                        if file.startswith('qmake') or file.startswith('qt'):
                            src_file = os.path.join(qt_path, file)
                            dst_file = os.path.join(qt_install_dir, 'bin', file)
                            if os.path.isfile(src_file):
                                shutil.copy2(src_file, dst_file)
                                c.print('>> Copied {} to qt/bin directory'.format(file))
                qt_found = True
        
        if qt_found:
            # 创建符号链接
            c.symlink(qt_install_dir, qt_dir)
            c.print('>> Qt setup completed via system package manager')
            
            # 验证安装
            try:
                result = subprocess.run(['qmake', '--version'], 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    c.print('>> Qt verification successful: {}'.format(result.stdout.strip()))
                else:
                    c.print('>> Qt verification failed: {}'.format(result.stderr))
            except Exception as e:
                c.print('>> Qt verification error: {}'.format(e))
        else:
            c.print('>> Error: Qt not found in system paths')
            exit(1)
            
    except Exception as e:
        c.print('>> Error installing Qt: {}'.format(e))
        exit(1)

elif os_name == 'win64':
    c.print('>> Installing Qt5 via chocolatey for Windows...')
    try:
        # 尝试使用chocolatey安装Qt
        result = subprocess.run(['choco', 'install', 'qt5', '--yes'], 
                             capture_output=True, text=True)
        if result.returncode == 0:
            c.print('>> Qt installed via chocolatey')
        else:
            c.print('>> Chocolatey installation failed, trying alternative method')
            
            # 尝试使用vcpkg安装Qt
            result = subprocess.run(['vcpkg', 'install', 'qt5'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                c.print('>> Qt installed via vcpkg')
            else:
                c.print('>> Vcpkg installation failed')
                
                # 如果包管理器都失败，尝试手动下载
                c.print('>> Trying manual Qt download for Windows...')
                qt_url = 'https://download.qt.io/official_releases/qt/5.15.2/5.15.2/single/qt-everywhere-src-5.15.2.tar.xz'
                qt_archive = 'qt-everywhere-src-5.15.2.tar.xz'
                
                try:
                    c.download(qt_url, qt_archive)
                    c.extract(qt_archive, '.')
                    c.print('>> Qt downloaded and extracted successfully')
                except Exception as e:
                    c.print('>> Manual Qt download failed: {}'.format(e))
                    exit(1)
        
        # 创建Qt目录结构
        qt_install_dir = 'qt'
        os.makedirs(qt_install_dir, exist_ok=True)
        
        # 查找Windows上的Qt安装
        qt_paths = [
            'C:/Qt/5.15.2/msvc2019_64',
            'C:/Qt/5.15.2/msvc2019',
            'C:/Qt/5.15.2/mingw81_64',
            'C:/Qt/5.15.2/mingw81',
            'C:/Program Files/Qt/5.15.2/msvc2019_64',
            'C:/Program Files (x86)/Qt/5.15.2/msvc2019_64'
        ]
        
        qt_found = False
        for qt_path in qt_paths:
            if os.path.exists(qt_path):
                c.print('>> Found Qt at: {}'.format(qt_path))
                import shutil
                shutil.copytree(qt_path, qt_install_dir, dirs_exist_ok=True)
                qt_found = True
                break
        
        if qt_found:
            # 创建符号链接
            c.symlink(qt_install_dir, qt_dir)
            c.print('>> Qt setup completed for Windows')
        else:
            c.print('>> Error: Qt not found in Windows paths')
            exit(1)
            
    except Exception as e:
        c.print('>> Error installing Qt on Windows: {}'.format(e))
        exit(1)

else:
    c.print('>> Unsupported OS: {}'.format(os_name))
    exit(1) 