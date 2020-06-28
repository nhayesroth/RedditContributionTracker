# from urllib.parse import quote_plus

import praw
import pdb
import configparser

from user import User
import utils

def get_top_level_comments(submission):
    submission.comments.replace_more(limit=0)
    return submission.comments

def construct_dict_from_top_level_comments(top_level_comments):
    """Scans the top-level comments and constructs a dictionary mapping(name -> User)."""
    users_by_name = dict()
    for comment in top_level_comments:
        # Ignore comments that have been deleted.
        # TODO: this is bad behavior. better would be to call them out or record the comment before it was deleted.
        if comment.author is None:
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
            print(f"{username} has asked {len(user.questions)} so far")

    return users_by_name

def scan_replies_to_top_level_comments(users_by_name):
    """Scans replies to top-level comments and updates the users_by_name dict."""
    repliers_by_name = dict()
    for username in users_by_name.keys():
        requestor = users_by_name.get(username)
        questions = requestor.questions
        for question in questions:
            replies = question.replies
            for reply in replies:
                if reply.author is None:
                    continue
                else:
                    # Update the requestor to track the number of replies they've received
                    requestor.inc_num_replies_to_questions()
                    # Update the replier to track their contributions
                    replier_name = reply.author.name
                    replier = repliers_by_name.get(replier_name, User(name=replier_name, questions=[], replies=[]))
                    replier.add_reply(reply)
                    repliers_by_name[replier_name] = replier
                    print(f"{username} has responded {len(replier.replies)} times so far ({utils.get_abbreviated_comment(reply)})")
    # Combine the 2 dictionaries
    for username in repliers_by_name:
        if username in users_by_name:
            requestor = users_by_name.get(username)
            replier = repliers_by_name.get(username)
            combined_user = User.combine(requestor, replier)
            users_by_name[username] = combined_user
    return users_by_name

def get_users_sorted_by_relative_contribution(users_by_name):
    """Returns a list of Users, sorted by their relative contribution (descending)."""
    users = list(users_by_name.values())
    users.sort(key=lambda user: user.relative_contribution(), reverse=True)
    return users


def get_submission():
    config = configparser.ConfigParser()
    config.read('config.ini')
    config = config['GLOBAL']
    reddit = praw.Reddit(
        user_agent=config['user_agent'],
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        username=config['username'],
        password=config['password'],
    )
    url = config['url']
    return reddit.submission(url=url)

def main():
    submission = get_submission()

    top_level_comments = get_top_level_comments(submission)
    users_by_name = construct_dict_from_top_level_comments(top_level_comments)
    users_by_name = scan_replies_to_top_level_comments(users_by_name)
    sorted_users = get_users_sorted_by_relative_contribution(users_by_name)

    for user in sorted_users:
        print(user)


if __name__ == "__main__":
    main()