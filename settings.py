import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--rootpath',  dest='rootpath', default=None,               help='Root Path for Find')
parser.add_argument('--file',  dest='fname', required=True,default=None,               help='File with permission information')
parser.add_argument('--groups',  dest='groups', required=True,default=None,               help='File with group information')
parser.add_argument('--rules',  dest='rules', default=None,               help='Rules to run')

global args
args = parser.parse_args()

