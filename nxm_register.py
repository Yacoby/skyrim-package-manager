import os
import sys
import platform
import subprocess

try:
    import win32com.shell.shell as shell
    import _winreg as winreg
except ImportError:
    if platform.system() == 'Windows':
        raise

NXM_DESKTOP_NAME = 'nxm.desktop'

def _get_run_cmd():
    if getattr(sys, 'frozen', False):
        return '"%s"' % sys.executable
    else:
        return '"%s" "%s"' % (sys.executable, os.path.abspath(sys.argv[0]))

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
    '''
    TODO why does this know how to start the program :(
    '''
    if sys.argv[-1] != '--regnxm':
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:] + ['--regnxm'])
        shell.ShellExecuteEx(lpVerb='runas', lpFile=sys.executable, lpParameters=params)
        return

    perms = winreg.KEY_WOW64_64KEY |  winreg.KEY_ALL_ACCESS
    with winreg.CreateKeyEx(winreg.HKEY_CLASSES_ROOT, r'nxm\DefaultIcon', 0, perms):
        winreg.SetValue(winreg.HKEY_CLASSES_ROOT, r'nxm\DefaultIcon', winreg.REG_SZ, '')

    with winreg.CreateKeyEx(winreg.HKEY_CLASSES_ROOT, r'nxm\shell\open\command', 0, perms):
        winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                        r'nxm\shell\open\command',
                        winreg.REG_SZ,
                        '%s "%%1"' % _get_run_cmd())

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
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'nxm\shell\open\command'):
            return _get_run_cmd() in winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, r'nxm\shell\open\command')
    except WindowsError:
        return False


def is_nxm_registered():
    f = {
            'Linux' : _is_nxm_registered_linux,
            'Windows' : _is_nxm_registered_windows,
    }
    return f[platform.system()]()

