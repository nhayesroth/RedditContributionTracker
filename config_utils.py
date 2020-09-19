import configparser
import getopt
import sys

def get_config(argv):
    """Gets all config options for the program, returning an object that maps <option, value>."""
    config = read_global_config();
    return add_command_line_args(config, argv)

def read_global_config():
    """Reads global config options from config.ini"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['GLOBAL']

def add_command_line_args(config, argv):
    """Adds command-line arguments to the given config and returns it."""
    try:
        opts, args = getopt.getopt(argv,"pq=",["print"])
    except getopt.GetoptError:
        print('Run in continuous mode:                     python3 main.py')
        print('Print results instead of posting to Reddit: python3 main.py -p')
        sys.exit(2)
    for opt, arg in opts:
       if opt in ("-p", "--print"):
        config['mode'] = 'print'
    return config