import argparse
import json
import os
import logger

"""Loads all variables for the task

- Prefers variables passed via command line.
- Falls back to environment variables.
- Errors out if any required variable is not set.
"""
def load_variables():
  # Initialize parser
  parser = argparse.ArgumentParser()
   
  # Bot-related arguments
  parser.add_argument(
    "--username",
    default = os.environ.get('username'),
    help = "The username of your bot's reddit account.")
  parser.add_argument(
    "--password",
    default = os.environ.get('password'),
    help = "The password for your bot's account")
  parser.add_argument(
    "--user_agent",
    default = os.environ.get('user_agent'),
    help = "User agent passed to PRAW (likely the name of your bot or a description of the specific application).")
  parser.add_argument(
    "--client_id",
    default = os.environ.get('client_id'),
    help = "The ID of your bot (see bot_creds_example.png).")
  parser.add_argument(
    "--client_secret",
    default = os.environ.get('client_secret'),
    help = "The secret of your bot (see bot_creds_example.png).")

  # Arguments related to selecting a post
  parser.add_argument(
    "--posts",
    default = os.environ.get('posts'),
    type = parse_posts,
    help = "JSON string describing one or more posts to target. See README for examples.")

  # Arguments that alter how a post is processed
  parser.add_argument(
    "--reply_threshold",
    default = os.environ.get('reply_threshold') or 3,
    help = "The minimum number of replies to a top-level comment before the bot considers it satisfied and stops including it in the results.")

  # Arguments that alter the final output
  parser.add_argument(
    "--mode",
    default = os.environ.get('mode') or 'print',
    help = "Either `print`, which will print results to the command line, or `post`, which will post results as a Reddit comment.")
  parser.add_argument(
    "--comment_mode",
    default = os.environ.get('comment_mode'),
    help = "Either `new`, which will delete the bot's previous comment and post a new one, or `edit`, which will edit the bot's previous comment.")
  parser.add_argument(
    "--interval",
    default = os.environ.get('interval') or 600,
    help = "The interval (in seconds) the bot will wait between scans. Note: this only affects the comment. Scheduling is actually handled by the Heroku Scheduler.")

  # Other (debug) arguments
  parser.add_argument(
    "--debug",
    default = False,
    help = "Prints additional debug messages that show the task's progress.")
  parser.add_argument(
    "--answer_username",
    default = os.environ.get('answer_username'),
    help = "Only include answers from 1 user.")
  parser.add_argument(
    "--question_username",
    default = os.environ.get('question_username'),
    help = "Only include questions from 1 user.")
  parser.add_argument(
    "--print_answers",
    help = "Prints scanned answers on the command-line.")
  parser.add_argument(
    "--print_questions",
    help = "Prints scanned questions on the command-line.")

  # Read arguments from command line
  args = parser.parse_args()

  return args


def parse_posts(string):
  """
  Parses a user-supplied string representing one or more target posts into a list of standard namespaces.
  
  For example, the user can supply a list containing using different styles to target two different posts:
  - (1) a subreddit and post title regex
  - (2) a specific post
  string = '[{ "subreddit": "foo", "post_regex": "bar" }, { "post_id": "zebra" }]'
  # =>
    [
      { subreddit: "foo", post_regex: "bar", post_id: None }
      { subreddit: None, post_regex: None, post_id": "zebra" }}
    ]

  Alternatively, the user can supply a single object that describes one target post:
  string = '{ "post_id": "hello world" }'
  # ->
    [
      { subreddit: None, post_regex: None, post_id": "hello world" }}
    ]
  """
  # Load the posts argument as a json object
  json_obj = json.loads(string)
  # If the json loads as a list, convert each object to its own post namespace.
  if isinstance(json_obj, list):
    list_of_post_dicts = json_obj
    return list(map(lambda post_dict: parse_post(post_dict), list_of_post_dicts))
  # If the json loads as object, convert that object to a post namespace and return a list it.
  elif isinstance(json_obj, dict):
    post_dict = json_obj
    return [parse_post(post_dict)]
  # Otherwise, the user supplied bad input.
  else:
    raise ValueError(
      f"Unable to parse posts. Please verify you provided valid json. Check the README for examples. Value you provided: {string}")

def parse_post(dict):
  return argparse.Namespace(
    post_id = dict.get('post_id'),
    post_regex = dict.get('post_regex'),
    subreddit = dict.get('subreddit'))