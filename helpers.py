import operator
import os
from pprint import pprint as pp
import re
import stat
import sublime
import sublime_plugin
import subprocess
import sys
import threading

SUPPORT_DIR_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'Support')

def exe(command, need_stdout=False, timeout=None, print_command=True, stdin_data=None):
    class Command(object):
        def __init__(self, cmd):
            self.cmd = cmd
            self.process = None
            self.out = None
            self.err = None
            self.returncode = None
            self.data = None

        def run(self, timeout, need_stdout, stdin_data):
            def target():
                use_shell = True if sys.platform == "win32" else False

                self.process = subprocess.Popen(
                    self.cmd,
                    # universal_newlines=True,
                    shell=use_shell,
                    stdin=subprocess.PIPE if need_stdout else None,
                    stdout=subprocess.PIPE if need_stdout else None,
                    stderr=subprocess.PIPE if need_stdout else None,
                    bufsize=0,
                )
                if need_stdout:
                    utf8_data = stdin_data
                    needs_encode = False
                    if sys.version_info[0] >= 3:
                        needs_encode = True
                    else:
                        needs_encode = utf8_data and isinstance(utf8_data, unicode)

                    # if needs_encode:
                    #     utf8_data = utf8_data.encode('utf-8')
                    # print(type(utf8_data))
                    outs, errs = self.process.communicate(utf8_data)

                    if outs:
                        self.out = outs.decode('utf-8')
                    if errs:
                        self.err = errs.decode('utf-8')
                else:
                    self.process.wait()

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(timeout)
            if thread.is_alive():
                self.process.terminate()
                thread.join()

            self.returncode = self.process.returncode
            return self.out, self.err

    if print_command:
        print(">> {cmd}".format(cmd=' '.join(command)))
    c = Command(command)
    c.run(timeout, need_stdout, stdin_data)
    if c.returncode != 0:
        msg = '"{cmd}" returned {code}'.format(cmd=' '.join(command),
                                               code=c.returncode)
        print(msg)
        if need_stdout:
            print(c.out)
            print(c.err)
        raise Exception(msg)
    return c.out


def git_exe(args):
    try:
        cmd = ['git'] + args
        result = exe(cmd, need_stdout=True)
        return '>> {cmd}\n\n{result}'.format(cmd=' '.join(cmd), result=result)
    except Exception as e:
        return "Unexpected error:\n\n" + str(e)


def ruby_exe(args):
    ruby_cmd = {
      'win32': "ruby.exe",
      'darwin': "ruby",
      'linux2': "ruby"
    }[sys.platform]
    cmd = [ruby_cmd] + args
    return exe(cmd)


def chmod_x_binary(binary):
    '''
    Failsafe to set exectuable bit on bundled binaries, after Package Manager
    unpacked them from .zip files
    '''
    if sys.platform != 'win32':
        st = os.stat(binary)
        os.chmod(binary, st.st_mode | stat.S_IEXEC)


def array_to_string(tokens, joiner):
    '''
    array_to_string(['1', '2', '3'], ' ') --> "'1' '2' '3'"
    array_to_string(['1', '2', '3'], ', ') --> "'1', '2', '3'"
    '''
    def escape_with_delim(text, delim):
        result = text.replace(delim, '\\' + delim)
        return delim + result + delim

    quotes_count = sum([i.count('"') for i in tokens])
    apostrophes_count = sum([i.count("'") for i in tokens])
    if quotes_count > apostrophes_count:
        delim = "'"
    else:
        delim = '"'
    return joiner.join([escape_with_delim(i, delim) for i in tokens])


def git_relative_file_path(file_name, branch_name):
    bare_name = exe(['git', 'ls-tree', '--full-name', branch_name, file_name], need_stdout=True)
    if not len(bare_name):
        raise Exception('%s not found in %s branch' % (file_name, branch_name))
    return (bare_name.split(' ')[2].split('\t')[1].rstrip())


def get_forked_from_file_path(full_file_name):
    relative_file_name = git_relative_file_path(full_file_name, 'HEAD')

    for line in open(full_file_name):
        match = re.search('\/\/ #forked-from: (.+)$', line)
        if match:
            relative_file_name = match.groups()[0]
        break

    return relative_file_name


# This function returns file path, relative to the chromium/src directory.
#
# It also understands fork markers and returns the path of the original forked
# file.
def get_chromium_file_path(full_file_name):
    relative_file_name = get_forked_from_file_path(full_file_name)

    # delete 'src/' portion of file name
    return '/'.join(relative_file_name.split('/')[1:])


def open_url(url):
    print(url)
    exe(['open', url])
    sublime.status_message(url + " is opened in Browser")
