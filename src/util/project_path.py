from os import path


def src_check(dir_name):
    return dir_name[::-1].index('crs') + 3


parent_dir_name = path.dirname(path.abspath(__file__))
if 'src' in parent_dir_name:
    modified_dir_name = parent_dir_name[:-src_check(parent_dir_name)]
    ROOT_DIR = path.abspath(modified_dir_name)
else:
    ROOT_DIR = parent_dir_name

CONFIG_FILE = path.join(ROOT_DIR, 'config.json')
