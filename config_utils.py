import configparser
import getopt
import pdb
import sys

def get_config(argv):
    """Gets all config options for the program, returning an object that maps <option, value>.

    Values can be retrieved from the object via config.get('key'). If the key is not present in the config,
    a `None` value is returned.
    """
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
        opts, args = getopt.getopt(
            argv,
            "pvq:a:",
            [
                "print",
                "once",
                "print_questions",
                "print_answers",
                "post_id=",
                "question_username=",
                "answer_username="
            ])
    except getopt.GetoptError:
        print('Run in continuous mode:                        python3 main.py')
        print('Run the task once:                             python3 main.py --once')
        print('Print results instead of posting to Reddit:    python3 main.py --post_id xjhasd7')
        print('Choose a post to scan (instead of config.ini): python3 main.py --post_id xjhasd7')
        print('Only include questions by 1 user:              python3 main.py -q interesting_user_name')
        print('Only include answers by 1 user:                python3 main.py -a interesting_user_name')
        print('Print scanned questions (for debugging):       python3 main.py --print_questions')
        print('Print scanned answers (for debugging):         python3 main.py --print_answers')
        sys.exit(2)
    for opt, arg in opts:
       if opt in ["-p", "--print"]:
        config['mode'] = 'print'
       if opt in ["--once"]:
        config['once'] = 'true'
       if opt in ["--print_questions"]:
        config['print_questions'] = 'true'
       if opt in ["--print_answers"]:
        config['print_answers'] = 'true'
       if opt in ["--post_id"]:
        config['post_id'] = arg
       if opt in ["-q", "--question_username"]:
        config['question_username'] = arg
       if opt in ["-a", "--answer_username"]:
        config['answer_username'] = arg
    return config