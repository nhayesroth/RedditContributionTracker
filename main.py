import configparser
import getopt
import praw
import sys
import threading
import time

import scheduler
from user import User
import utils

def get_top_level_comments(submission):
    submission.comments.replace_more(limit=0)
    return submission.comments

def construct_dict_from_top_level_comments(top_level_comments, bot_username):
    """Scans the top-level comments and constructs a dictionary mapping(name -> User)."""
    users_by_name = dict()
    for comment in top_level_comments:
        # Ignore comments that have been deleted.
        # TODO: this is bad behavior. better would be to call them out or record the comment before it was deleted.
        if comment.author is None:
            continue
        elif comment.author.name == bot_username:
            continue
        else:
            username = comment.author.name
            if username in users_by_name.keys():
                user = users_by_name.get(username)
            else:
                user = User(name=username, questions=[])
            user = users_by_name.get(username, User(name=username, questions=[]))
            user.add_question(comment)
            users_by_name[username] = user

    return users_by_name

def scan_replies_to_top_level_comments(users_by_name, bot_username):
    """Scans replies to top-level comments and updates the users_by_name dict."""
    repliers_by_name = dict()
    for username in users_by_name.keys():
        requestor = users_by_name.get(username)
        questions = requestor.questions
        for question in questions:
            replies = question.refresh().replies
            for reply in replies:
                if reply.author is None:
                    # Ignore deleted responses
                    continue
                elif reply.author.name == bot_username:
                    continue
                else:
                    # Update the requestor to track the number of replies they've received
                    requestor.inc_num_replies_to_questions()
                    # Update the replier to track their contributions
                    replier_name = reply.author.name
                    replier = repliers_by_name.get(replier_name, User(name=replier_name, questions=[], replies=[]))
                    replier.add_reply(reply)
                    repliers_by_name[replier_name] = replier
    # Combine the 2 dictionaries
    for username in repliers_by_name:
        replier = repliers_by_name.get(username)
        if username in users_by_name:
            requestor = users_by_name.get(username)
            combined_user = User.combine(requestor, replier)
            users_by_name[username] = combined_user
        else:
            users_by_name[username] = replier
    return users_by_name

def get_users_sorted_by_relative_contribution(users_by_name):
    """Returns a list of Users, sorted by their relative contribution (descending)."""
    users = list(users_by_name.values())
    users.sort(key=lambda user: user.relative_contribution(), reverse=True)
    return users

def get_users_sorted_by_replies(users_by_name):
    """Returns a list of Users, sorted by their relative contribution (descending)."""
    users = list(users_by_name.values())
    users.sort(key=lambda user: user.num_replies(), reverse=True)
    return users

def get_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['GLOBAL']

def get_reddit_instance(config):
    return praw.Reddit(
        user_agent=config['user_agent'],
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        username=config['username'],
        password=config['password'],
        validate_on_submit=True,
    )

def get_submission(reddit_instance, config):
    subreddit = reddit_instance.subreddit(config['subreddit'])
    for submission in subreddit.hot(limit=10):
        if utils.is_target_post(submission, config):
            return submission
    raise ValueError('Unable to find target post. Check the subreddit and post_regex in config.ini')

def post(submission, response, username):
    top_level_comments = get_top_level_comments(submission)
    for comment in top_level_comments:
        if comment.author is None:
            continue
        elif comment.author.name == username:
            comment.edit(response)
            print(f"Edited previous comment at {time.ctime(time.time())}: {comment.permalink}")
            return
    comment = submission.reply(response)
    print(f"Posted new comment at {time.ctime(time.time())}: {comment.permalink}")


def task(config):
    reddit_instance = get_reddit_instance(config)
    submission = get_submission(reddit_instance, config)

    top_level_comments = get_top_level_comments(submission)
    users_by_name = construct_dict_from_top_level_comments(
        top_level_comments, config['username'])
    users_by_name = scan_replies_to_top_level_comments(
        users_by_name, config['username'])

    users_sorted_by_contribution = get_users_sorted_by_relative_contribution(users_by_name)
    users_sorted_by_replies = get_users_sorted_by_replies(users_by_name)

    reply_threshold = 3
    interval = int(config['interval'])
    response = (f"\nResults will update every ~{utils.get_human_readable_time(interval)}.\n"
                "\n-----\n"
                "\nThe following users have helped the most people in this thread:\n"
                f"\n{utils.get_most_helpful_summary(users_sorted_by_replies)}\n"
                "\n-----\n"
                f"\nThe following users have helped the most people in this thread, but have fewer than {reply_threshold} replies to their own question(s):\n"
                f"\n{utils.get_most_helpful_without_replies_summary(users_sorted_by_replies, reply_threshold)}\n")
    
    if config['print_or_post'] == 'post':
        post(submission, response, config['username'])
    elif config['print_or_post'] == 'print':
        print(response)
    else:
      print('Unsupported print_or_post: ' + print_or_post)
      sys.exit(2)

def main(argv):
    print_or_post = 'post'
    try:
        opts, args = getopt.getopt(argv,"p",["print"])
    except getopt.GetoptError:
        print('Run in continuous mode:                     python3 main.py')
        print('Print results instead of posting to Reddit: python3 main.py -p')
        sys.exit(2)
    for opt, arg in opts:
       if opt in ("-p", "--print"):
          print_or_post = 'print'

    config = get_config()
    config['print_or_post'] = print_or_post

    # If targetting a single user or running in print mode => just run the task once.
    if print_or_post == 'print':
        task(config)
        return
    else:
        # Otherwise, run continuously on an interval.
        interval = int(config['interval']);
        threading.Thread(target=lambda: scheduler.every(interval, task, config)).start()

if __name__ == "__main__":
    main(sys.argv[1:])
