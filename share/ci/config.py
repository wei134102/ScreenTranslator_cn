from os import getenv, path
import re

app_name = 'ScreenTranslator'

target_name = app_name
qt_version = '5.15.2'
# 尝试使用更稳定的Qt版本
# qt_version = '5.15.0'
qt_modules = ['qtbase', 'qttools', 'icu',
              'qttranslations', 'qtx11extras', 'qtwebengine', 'qtwebchannel',
              'qtdeclarative', 'qtlocation', 'opengl32sw', 'd3dcompiler_47',
              'qtserialport']
qt_dir = path.abspath('qt')
ssl_dir = path.abspath('ssl')

build_dir = path.abspath('build')
dependencies_dir = path.abspath('deps')
pro_file = path.abspath(path.dirname(__file__) +
                        '/../../screen-translator.pro')
test_pro_file = path.abspath(path.dirname(__file__) +
                             '/../../tests/tests.pro')
bin_name = 'screen-translator'
app_version = 'testing'
with open(pro_file, 'r') as f:
    match = re.search(r'VER=(.*)', f.read())
    if match:
        app_version = match.group(1)
ts_files_dir = path.abspath(path.dirname(__file__) + '/../../translations')

os_name = getenv('OS', 'linux')
app_version += {'linux': '', 'macos': '-experimental',
                'win32': '', 'win64': ''}[os_name]
bitness = '32' if os_name == 'win32' else '64'
msvc_version = getenv('MSVC_VERSION', 'C:/Program Files (x86)/Microsoft Visual Studio/2019/Community')

build_type = 'release' # 'debug'
