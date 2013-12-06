import re
import sublime
import sublime_plugin
import urllib

from helpers import *

def parse_repository_url(s):
    #TODO(kirr) support different types of git url
    expr = r'(\w+://)?git@(?P<host>[\w\.]+):?/?(?P<project>[\w\~]+)/(?P<repo>\w+)\.git'
    match = re.match(expr, s)
    if match is None:
        print 'parsing failed'
        return ('','','')

    host = match.group("host")
    project = match.group("project")
    repo = match.group("repo")
    return (host, project, repo)

def get_relative_path(file_path, folder_list):
    for folder in folder_list:
        if file_path.startswith(folder):
            file_path = file_path[len(folder)+1:]
            break
    file_path = file_path.replace('\\', '/')
    return file_path

def get_current_window_relative_path(full_path):
    active_window = sublime.active_window()
    folder_list = [] if active_window is None else active_window.folders()
    file_path = get_relative_path(full_path, folder_list)
    return file_path

def get_current_line(view):
    first_selection = view.sel()[0]
    line_column = view.rowcol(first_selection.begin())
    return line_column[0] + 1

class CopyRelativeFilePathCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_path = get_current_window_relative_path(self.view.file_name())
        sublime.set_clipboard(file_path)

class CopyDebuggerBreakCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_path = get_current_window_relative_path(self.view.file_name())
        current_line = get_current_line(self.view)

        lldb_command = 'breakpoint set --file {0} --line {1}'.format(file_path, current_line)
        sublime.set_clipboard(lldb_command)

class CopyStashLinkToFileLineCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_path = self.view.file_name()
        os.chdir(os.path.dirname(file_path))
        root_folder = exe(['git', 'rev-parse', '--show-toplevel'], need_stdout=True).strip()

        file_path = get_relative_path(file_path, [root_folder])
        current_branch = exe(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], need_stdout=True).strip()
        repo_url = exe(['git', 'config', '--get', 'remote.origin.url'], need_stdout=True)
        current_line = get_current_line(self.view)

        host, project, repo = parse_repository_url(repo_url)
        if host != 'stash.desktop.dev.yandex.net':
            print 'stash server url is invalid'
            return

        url_params = '?at={0}'.format(urllib.quote_plus('refs/heads/' + current_branch))
        url = 'https://{0}/projects/{1}/repos/{2}/browse/{3}{4}#{5}'.format(host, project, repo, file_path, url_params, current_line)
        sublime.set_clipboard(url)

