import getopt
import praw
import sys
import threading
import time
import pdb

import scheduler
from user import User
import config_utils
import utils

def get_top_level_comments(submission):
  submission.comments.replace_more(limit=None)
  return submission.comments

def construct_dict_from_top_level_comments(top_level_comments, config):
  """Scans the top-level comments and constructs a dictionary mapping(name -> User)."""
  bot_username = config.get('username')
  question_username = config.get('question_username')
  print_questions = config.get('print_questions')

  users_by_name = dict()
  for comment in top_level_comments:
    # Ignore comments that have been deleted.
    # TODO: this is bad behavior. better would be to call them out or record the comment before it was deleted.
    if comment.author is None:
      continue
    elif comment.author.name == bot_username:
      continue
    elif question_username and comment.author.name != question_username:
      # Command-line specified a question_username => ignore other users' questions.
      continue
    else:
      # This is a real user => check if we've already encountered them then update the dict with their question.
      username = comment.author.name
      if username in users_by_name.keys():
        # This user has posted multiple questions. Retrieve their object so we can accumulate their questions.
        user = users_by_name.get(username)
      else:
        # This is the first question we've seen from this user. Construct a new object.
        user = User(name=username, questions=[])
      # Add the updated User object to our dict.
      user = users_by_name.get(username, User(name=username, questions=[]))
      user.add_question(comment)
      users_by_name[username] = user
      # if print_questions:
      #   print(f"Question - {username} - {utils.get_abbreviated_comment(comment)}")

  if print_questions:
    print('\n----Questions----')
    for username in users_by_name.keys():
      print(f"User: {username}")
      for question in users_by_name.get(username).questions:
        print(f"\t{utils.get_abbreviated_comment(question)}")
        
  return users_by_name

def scan_replies_to_top_level_comments(users_by_name, config):
  """Scans replies to top-level comments and updates the users_by_name dict."""
  bot_username = config.get('username')
  answer_username = config.get('answer_username')
  print_answers = config.get('print_answers')

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
        elif answer_username and reply.author.name != answer_username:
          # Command-line specified an answer_username => ignore other users answers.
          continue
        else:
          # Update the requestor to track the number of replies they've received
          requestor.inc_num_replies_to_questions()
          # Update the replier to track their contributions
          replier_name = reply.author.name
          replier = repliers_by_name.get(replier_name, User(name=replier_name, questions=[], replies=[]))
          replier.add_reply(reply)
          repliers_by_name[replier_name] = replier

  if print_answers:
    print('\n----Answers----')
    for username in repliers_by_name.keys():
      print(f"User: {username}")
      for reply in repliers_by_name.get(username).replies:
        print(f"\t{utils.get_abbreviated_comment(reply)}")
        print(f"\t\t(answers) - {reply.parent().author.name} - {utils.get_abbreviated_comment(reply.parent())}")

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

def get_users_sorted_by_replies(users_by_name):
  """Returns a list of Users, sorted by the answers they've contributed (descending).

  Filters any users that have not contributed anything.
  """
  users = [user for user in list(users_by_name.values()) if user.num_replies() > 0]
  users.sort(key=lambda user: user.num_replies(), reverse=True)
  return users

def get_reddit_instance(config):
  return praw.Reddit(
    user_agent=config.get('user_agent'),
    client_id=config.get('client_id'),
    client_secret=config.get('client_secret'),
    username=config.get('username'),
    password=config.get('password'),
    validate_on_submit=True,
  )

def get_submission(reddit_instance, config):
  if (config.get('post_id')):
    return reddit_instance.submission(id=config.get('post_id'))
  
  subreddit = reddit_instance.subreddit(config.get('subreddit'))
  for submission in subreddit.hot(limit=10):
    if utils.is_target_post(submission, config):
      return submission
  raise ValueError('Unable to find target post. Check the subreddit and post_regex in config.ini')

def post(submission, response, username):
  """Posts the response to Reddit.
  - If the bot hasn't posted a top-level comment in the thread, yet, a new comment will be posted.
  - If the bot already has a top-level comment, that comment will be edited with the new results.
  
  TODO: this isn't very efficient and sort of gimps the bot. would be better to track the comment ID
  and replace it directly
  """
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
  users_by_name = construct_dict_from_top_level_comments(top_level_comments, config)
  users_by_name = scan_replies_to_top_level_comments(users_by_name, config)

  users_sorted_by_replies = get_users_sorted_by_replies(users_by_name)

  reply_threshold = 3
  interval = int(config.get('interval'))
  response = (f"\nResults will update every ~{utils.get_human_readable_time(interval)}.\n"
        "\n-----\n"
        "\nThe following users have helped the most people in this thread:\n"
        f"\n{utils.get_most_helpful_summary(users_sorted_by_replies)}\n"
        "\n-----\n"
        f"\nThe following users have helped the most people in this thread, but have fewer than {reply_threshold} replies to their own question(s):\n"
        f"\n{utils.get_most_helpful_without_replies_summary(users_sorted_by_replies, reply_threshold)}\n")
  
  if config.get('mode') == 'post':
    post(submission, response, config.get('username'))
  else:
    print(response)

def main(argv):
  config = config_utils.get_config(argv)

  # If running in print mode => just run the task once.
  if config['mode'] == 'print':
    task(config)
    return
  else:
    # Otherwise, run the task once immediately.
    task(config)
    # And schedule future runs on an interval.
    interval = int(config.get('interval'));
    threading.Thread(target=lambda: scheduler.every(interval, task, config)).start()

if __name__ == "__main__":
  main(sys.argv[1:])
