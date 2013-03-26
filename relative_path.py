import sublime
import sublime_plugin


def get_relative_path(file_path, folder_list):
    for folder in folder_list:
        if file_path.startswith(folder):
            file_path = '.' + file_path[len(folder):]
            break
    return file_path


class CopyRelativeFilePathCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        active_window = sublime.active_window()
        folder_list = [] if active_window is None else active_window.folders()
        file_path = get_relative_path(self.view.file_name(), folder_list)
        file_path = file_path.replace('\\', '/')
        sublime.set_clipboard(file_path)
