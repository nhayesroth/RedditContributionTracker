import copy
import praw
import sys
import threading
import time
import re

import logger
import utils
import var_utils

from user import User

class Task:
  def __init__(self, vars):
    self.vars = vars

  def execute(self):
    """Top-level task definition.

    Scans a reddit thread, organizes users by contribution, then posts/prints the results.
    """
    logger.log(f"Task starting...", self.vars, True)
    self.vars.start_time = time.time()
    submission = self.get_submission()
    top_level_comments = self.get_top_level_comments(submission)    
    users_by_name = self.construct_dict_from_top_level_comments(top_level_comments)    
    users_by_name = self.scan_replies_to_top_level_comments(users_by_name)    
    users_sorted_by_replies = self.get_users_sorted_by_replies(users_by_name)
    response = self.construct_response(users_sorted_by_replies)    
    self.print_or_post(submission, top_level_comments, response)
    logger.log(
      f"Task finished in {time.strftime('%Mm%Ss', time.gmtime(time.time() - self.vars.start_time))}",
      self.vars,
      True)

  def get_submission(self):
    reddit_instance = praw.Reddit(
      user_agent=self.vars.user_agent,
      client_id=self.vars.client_id,
      client_secret=self.vars.client_secret,
      username=self.vars.username,
      password=self.vars.password,
      validate_on_submit=True)

    # If a post_id is supplied, retrieve it direcly.
    if (self.vars.post_id):
      submission = reddit_instance.submission(id = self.vars.post_id)
      logger.log(f"Retrieved submission by ID: {self.vars.post_id}", self.vars)
      return submission
    
    # Otherwise, use supplied subreddit and post_regex to find it amongst hot and stickied posts.
    if (self.vars.subreddit and self.vars.post_regex):
      subreddit = reddit_instance.subreddit(self.vars.subreddit)
      for submission in subreddit.hot(limit=10):
        if re.search(self.vars.post_regex, submission.title):
          logger.log(f"Successfully found submission: {submission.title} ({submission.permalink})", self.vars)
          return submission

    # Otherwise, throw an error.
    raise ValueError(
      f"Unable to find target post. Check the the post_id ({self.vars.post_id}), subreddit ({self.vars.subreddit}), and post_regex ({self.vars.post_regex}) variables.")

  def get_top_level_comments(self, submission):
    logger.log(f"Retrieving top-level comments...", self.vars)
    submission.comments.replace_more(limit=None)
    
    logger.log(f"Retrieved {submission.comments.__len__()} top-level comments", self.vars)
    return submission.comments

  def construct_dict_from_top_level_comments(self, top_level_comments):
    """Scans the top-level comments and constructs a dictionary mapping(name -> User)."""
    logger.log(f"Constructing a username dictionary from top-level comments...", self.vars)
    bot_username = self.vars.username
    question_username = self.vars.question_username
    print_questions = self.vars.print_questions

    users_by_name = dict()
    for comment in top_level_comments:
      # Ignore comments that have been deleted.
      if comment.author is None:
        continue
      # Ignore comments made by the bot, itself.
      elif comment.author.name == bot_username:
        continue
      # Command-line specified a question_username => ignore other users' questions.
      elif question_username and comment.author.name != question_username:
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

    if print_questions:
      print('\n----Questions----')
      for username in users_by_name.keys():
        print(f"User: {username}")
        for question in users_by_name.get(username).questions:
          print(f"\t{utils.get_abbreviated_comment(question)}")
          
    logger.log(f"Dictionary includes {len(users_by_name)} users", self.vars)
    return users_by_name

  def scan_replies_to_top_level_comments(self, users_by_name):
    """Scans replies to top-level comments and updates the users_by_name dict."""
    logger.log(f"Scanning replies to top-level comments...", self.vars)
    bot_username = self.vars.username
    answer_username = self.vars.answer_username
    print_answers = self.vars.print_answers

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
            # Ignore any reply by the bot.
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

    logger.log(f"Found replies from {len(repliers_by_name)} users", self.vars)
    logger.log(f"Dictionary now includes {len(users_by_name)} users", self.vars)

    return users_by_name

  def get_users_sorted_by_replies(self, users_by_name):
    """Returns a list of Users, sorted by the answers they've contributed (descending).

    Filters any users that have not contributed anything.
    """
    logger.log("Sorting users by how many replies they've made...", self.vars)
    users = [user for user in list(users_by_name.values()) if user.num_replies() > 0]
    users.sort(key=lambda user: user.num_replies(), reverse=True)
    return users

  def construct_response(self, users_sorted_by_replies):
    logger.log("Constructing response...", self.vars)
    interval = int(self.vars.interval)
    reply_threshold = int(self.vars.reply_threshold)

    return (f"\nResults will update every ~{utils.get_human_readable_time(interval)}.\n"
      "\n-----\n"
      "\nThe following users have helped the most people in this thread:\n"
      f"\n{utils.get_most_helpful_summary(users_sorted_by_replies)}\n"
      "\n-----\n"
      f"\nThe following users have helped the most people in this thread, but have fewer than {reply_threshold} replies to their own question(s):\n"
      f"\n{utils.get_most_helpful_without_replies_summary(users_sorted_by_replies, reply_threshold)}\n")

  def print_or_post(self, submission, top_level_comments, response):
    logger.log("Printing or posting response...", self.vars)
    if self.vars.mode == 'post':
      self.post(submission, top_level_comments, response)
    elif self.vars.mode == 'print':
      logger.log(f"Printing response: \n{response}", self.vars, True)
      logger.log(f"Response printed at {time.ctime(time.time())}", self.vars)
    else:
      raise ValueError(f"Unexpected mode ({self.vars.mode}). Should be either `post` or `print`.")

  def post(self, submission, top_level_comments, response):
    """Posts the response to Reddit.

    Behavior depends on comment_mode environment variable:
    - When comment_mode = 'edit'
      - If the bot already has a top-level comment, that comment will be edited with the new results.
      - If the bot hasn't posted a top-level comment in the thread, yet, a new comment will be posted.
    - When comment_mode = 'new'
      - If the bot already has a top-level comment, that comment will be deleted.
      - A new comment will be posted.
    """
    logger.log("Posting response...", self.vars)
    bot_name = self.vars.username
    for comment in top_level_comments:
      if comment.author is None:
        continue
      elif comment.author.name == bot_name:
        comment_mode = self.vars.comment_mode
        if comment_mode == 'edit':
          comment.edit(response)
          logger.log(f"Edited previous comment at {time.ctime(time.time())}: {comment.permalink}", self.vars, True)
          return
        elif comment_mode == 'new':
          comment.delete()
          logger.log(f"Deleted previous comment at {time.ctime(time.time())}: {comment.permalink}", self.vars, True)
          continue
        else:
          raise ValueError('Unexpected comment_mode: ' + comment_mode)
    comment = submission.reply(response)
    logger.log(f"Posted new comment at {time.ctime(time.time())}: {comment.permalink}", self.vars, True)

def main(argv):
  vars = var_utils.load_variables()
  # Spawn a separate thread to handle each of the target posts in parallel.
  for post in vars.posts:
    # Make a copy of the program's vars for each thread and set the target post info for that thread.
    task_vars = copy.deepcopy(vars)
    task_vars.post_id = post.post_id
    task_vars.post_regex = post.post_regex
    task_vars.subreddit = post.subreddit
    task_vars.posts = None
    task = Task(task_vars)

    threading.Thread(target = task.execute).start()
  return

if __name__ == "__main__":
  main(sys.argv[1:])
