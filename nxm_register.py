import os
import sys
import platform
import subprocess

try:
    import win32com.shell.shell as shell
    import _winreg as winreg
except ImportError:
    pass

ASADMIN = 'asadmin'

NXM_DESKTOP_NAME = 'nxm.desktop'

MAIN_PYTHON_FILE = 'main.py'

def _get_run_cmd():
    return sys.executable + ' ' + os.path.join(os.getcwd(), MAIN_PYTHON_FILE)

def _get_desktop_file_path():
    app_path = os.path.expanduser('~/.local/share/applications')
    return os.path.join(app_path, NXM_DESKTOP_NAME)

def _register_nxm_handler_linux():
    desktop_file = (
'''[Desktop Entry]
Name=Nexus Mod
Type=Application
MimeType=x-scheme-handler/nxm;
Exec=''')
    desktop_file += _get_run_cmd() + ' %u'

    dest = _get_desktop_file_path()
    with open(dest, 'w') as fp:
        fp.write(desktop_file)

    os.system('xdg-mime default %s x-scheme-handler/nxm' % NXM_DESKTOP_NAME)

def _register_nxm_handler_windows():
    with winreg.CreateKeyEx(winreg.HKEY_CLASSES_ROOT, r'nxm\DefaultIcon', 0, winreg.KEY_WOW64_64KEY |  winreg.KEY_ALL_ACCESS) as k:
        winreg.SetValue(winreg.HKEY_CLASSES_ROOT, r'nxm\DefaultIcon', winreg.REG_SZ, '')

    with winreg.CreateKeyEx(winreg.HKEY_CLASSES_ROOT, r'nxm\shell\open\command', 0, winreg.KEY_WOW64_64KEY |  winreg.KEY_ALL_ACCESS) as k:
        winreg.SetValue(winreg.HKEY_CLASSES_ROOT, r'nxm\shell\open\command', winreg.REG_SZ, '"%s" "%%1"' % _get_run_cmd())

def register_nxm_handler():
    f = {
            'Linux' : _register_nxm_handler_linux,
            'Windows' : _register_nxm_handler_windows,
    }
    f[platform.system()]()

def _is_nxm_registered_linux():
    proc_and_args = 'xdg-mime query default x-scheme-handler/nxm'
    process = subprocess.Popen(proc_and_args, stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()

    if NXM_DESKTOP_NAME not in output:
        return False

    dest = _get_desktop_file_path()

    try:
        with open(dest) as fp:
            contents = fp.read()
            return _get_run_cmd() in contents
    except IOError:
        return False

def _is_nxm_registered_windows():
    return False

def is_nxm_registered():
    f = {
            'Linux' : _is_nxm_registered_linux,
            'Windows' : _register_nxm_handler_windows,
    }
    return f[platform.system()]()

if __name__ == '__main__':
    if sys.argv[-1] != ASADMIN:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:] + [ASADMIN])
        shell.ShellExecuteEx(lpVerb='runas', lpFile=sys.executable, lpParameters=params)
        sys.exit(0)
    _register_nxm_handler_windows()
