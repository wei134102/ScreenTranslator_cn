import common as c
from config import qt_modules, qt_version, qt_dir, os_name
import sys
import xml.etree.ElementTree as ET
import os

c.print('>> Downloading Qt {} ({}) for {}'.format(
    qt_version, qt_modules, os_name))

# 确保当前目录存在
c.print('>> Current working directory: {}'.format(os.getcwd()))
c.print('>> Current directory contents:')
for item in os.listdir('.'):
    c.print('  - {}'.format(item))

# 显示配置信息
c.print('>> OS name: {}'.format(os_name))
c.print('>> Kit architecture: {}'.format(kit_arch))
c.print('>> Qt directory prefix: {}'.format(qt_dir_prefix))

if os_name == 'linux':
    os_url = 'linux_x64'
    kit_arch = 'gcc_64'
    qt_dir_prefix = '{}/gcc_64'.format(qt_version)
elif os_name == 'win32':
    os_url = 'windows_x86'
    kit_arch = 'win32_msvc2019'
    qt_dir_prefix = '{}/msvc2019'.format(qt_version)
elif os_name == 'win64':
    os_url = 'windows_x86'
    kit_arch = 'win64_msvc2019_64'
    qt_dir_prefix = '{}/msvc2019_64'.format(qt_version)
    # Windows上可能需要不同的架构名称
    if not any(kit_arch in name for name in ['qtbase', 'qttools']):
        kit_arch = 'win64_msvc2019'
elif os_name == 'macos':
    os_url = 'mac_x64'
    kit_arch = 'clang_64'
    qt_dir_prefix = '{}/clang_64'.format(qt_version)

qt_version_dotless = qt_version.replace('.', '')
base_url = 'https://download.qt.io/online/qtsdkrepository/{}/desktop/qt5_{}' \
    .format(os_url, qt_version_dotless)
updates_file = 'Updates-{}-{}.xml'.format(qt_version, os_name)

c.print('>> Downloading updates file from: {}'.format(base_url + '/Updates.xml'))
try:
    c.download(base_url + '/Updates.xml', updates_file)
except Exception as e:
    c.print('>> Error downloading updates file: {}'.format(e))
    # 尝试备用URL
    backup_url = 'https://download.qt.io/online/qtsdkrepository/{}/desktop/qt5_{}/Updates.xml' \
        .format(os_url, qt_version_dotless)
    c.print('>> Trying backup URL: {}'.format(backup_url))
    c.download(backup_url, updates_file)

updates = ET.parse(updates_file)
updates_root = updates.getroot()
all_modules = {}
for i in updates_root.iter('PackageUpdate'):
    name = i.find('Name').text
    if 'debug' in name or not kit_arch in name:
        continue

    archives = i.find('DownloadableArchives')
    if archives.text is None:
        continue

    archives_parts = archives.text.split(',')
    version = i.find('Version').text
    for archive in archives_parts:
        archive = archive.strip()
        parts = archive.split('-')
        module_name = parts[0]
        all_modules[module_name] = {'package': name, 'file': version + archive}

if len(sys.argv) > 1:  # handle subcommand
    if sys.argv[1] == 'list':
        c.print('Available modules:')
        for k in iter(sorted(all_modules.keys())):
            c.print(k, '---', all_modules[k]['file'])
    exit(0)

c.print('>> Available modules:')
for k in iter(sorted(all_modules.keys())):
    c.print('  - {}: {}'.format(k, all_modules[k]['file']))

c.print('>> Required modules:')
for module in qt_modules:
    c.print('  - {}'.format(module))

# 先尝试下载一个小的模块进行测试
test_modules = ['qtbase']  # 只下载基础模块进行测试
c.print('>> Testing with minimal modules: {}'.format(test_modules))

for module in test_modules:
    if module not in all_modules:
        c.print('>> Required module {} not available'.format(module))
        c.print('>> Available modules:')
        for k in iter(sorted(all_modules.keys())):
            c.print('    - {}'.format(k))
        continue
    file_name = all_modules[module]['file']
    package = all_modules[module]['package']
    c.print('>> Downloading test module: {} -> {}'.format(module, file_name))
    try:
        c.download(base_url + '/' + package + '/' + file_name, file_name)
        c.extract(file_name, '.')
        c.print('>> Test module downloaded successfully')
    except Exception as e:
        c.print('>> Error downloading test module: {}'.format(e))
        exit(1)

# 如果测试成功，继续下载其他模块
c.print('>> Test successful, downloading all modules...')
for module in qt_modules:
    if module in test_modules:  # 跳过已经下载的测试模块
        continue
    if module not in all_modules:
        c.print('>> Required module {} not available'.format(module))
        c.print('>> Available modules:')
        for k in iter(sorted(all_modules.keys())):
            c.print('    - {}'.format(k))
        continue
    file_name = all_modules[module]['file']
    package = all_modules[module]['package']
    c.print('>> Downloading module: {} -> {}'.format(module, file_name))
    c.download(base_url + '/' + package + '/' + file_name, file_name)
    c.extract(file_name, '.')

# 检查Qt目录是否存在
if not os.path.exists(qt_dir_prefix):
    c.print('>> Error: Qt directory not found: {}'.format(qt_dir_prefix))
    c.print('>> Available directories:')
    import glob
    for dir in glob.glob('*'):
        if os.path.isdir(dir):
            c.print('  - {}'.format(dir))
    exit(1)

c.symlink(qt_dir_prefix, qt_dir)

c.print('>> Updating license')
config_name = qt_dir + '/mkspecs/qconfig.pri'
if os.path.exists(config_name):
    config = ''
    try:
        with open(config_name, 'r', encoding='utf-8') as f:
            config = f.read()
    except UnicodeDecodeError:
        try:
            with open(config_name, 'r', encoding='latin-1') as f:
                config = f.read()
        except Exception as e:
            c.print('>> Warning: Could not read config file: {}'.format(e))
            return

    config = config.replace('Enterprise', 'OpenSource')
    config = config.replace('licheck.exe', '')
    config = config.replace('licheck64', '')
    config = config.replace('licheck_mac', '')

    try:
        with open(config_name, 'w', encoding='utf-8') as f:
            f.write(config)
    except Exception as e:
        c.print('>> Warning: Could not write config file: {}'.format(e))
else:
    c.print('>> Warning: qconfig.pri not found, skipping license update')
