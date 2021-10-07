import argparse
import os
from debug import log

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
    "--subreddit",
    default = os.environ.get('subreddit'),
    help = "The subreddit the bot will search for the the thread matching.")  
  parser.add_argument(
    "--post_regex",
    default = os.environ.get('post_regex'),
    help = "A python regex to match the reddit post your bot will scan.")  
  parser.add_argument(
    "--post_id",
    default = os.environ.get('post_id'),
    help = "Choose a specific post to scan (instead of subreddit and post_regex).")

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
  
  log(args, args)

  return args
