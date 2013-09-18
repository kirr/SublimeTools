import sublime
import sublime_plugin


def get_relative_path(file_path, folder_list):
    for folder in folder_list:
        if file_path.startswith(folder):
            file_path = '.' + file_path[len(folder):]
            break
    return file_path


class CopyDebuggerBreakCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        active_window = sublime.active_window()
        folder_list = [] if active_window is None else active_window.folders()
        file_path = get_relative_path(self.view.file_name(), folder_list)
        file_path = file_path.replace('\\', '/')

        first_selection = self.view.sel()[0]
        line_column = self.view.rowcol(first_selection.begin())

        lldb_command = 'breakpoint set --file {0} --line {1}'.format(file_path, line_column[0])
        sublime.set_clipboard(lldb_command)
