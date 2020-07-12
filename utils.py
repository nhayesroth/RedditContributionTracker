import re
from copy import deepcopy
import time 

"""Returns the first 20 chars of a comment with whitespaces replaced by single-space chars."""
def get_abbreviated_comment(comment):
    return re.sub(r"\s+", " ", comment.body[0 : 20], flags=re.UNICODE)

"""Returns whether the specified submission is our target.

In our case this means 2 things:
- The post is stickied
- The post title matches the post_regex in config.ini
"""
def is_target_post(submission, config):
    regular_expression_object = re.compile(config['post_regex'])
    return submission.stickied and regular_expression_object.match(submission.title)

def get_most_helpful_summary(users):
  summary = ("User | # Helped"
            "\n----|:-----:|:-----:|")
  for user in users[:10]:
    summary += f"\n{user.get_profile_link_string()} | {user.num_replies()}"
  return summary

def get_most_helpful_without_replies_summary(users, reply_threshold):
  filtered_users = []
  # Filter the list of helpful users to only those with top-level comments
  # that are under the reply_threshold
  for user in users:
    if len(filtered_users) >= 10:
      break
    questions_that_could_use_some_love = []
    for question in user.questions:
      replies = question.replies
      if len(replies) < reply_threshold:
        # Only include questions under the threshold
        questions_that_could_use_some_love.append(question)
    if len(questions_that_could_use_some_love) > 0:
      filtered_users.append({
        'name': user.get_profile_link_string(),
        'num_helped': user.num_replies(),
        'questions_that_could_use_some_love': questions_that_could_use_some_love
      })

  # Produce the summary string
  summary = ("User | # Helped | Questions that could use some love"
            "\n----|:-----:|:-----:|")
  for user in filtered_users:
    summary += f"\n{user['name']} | {user['num_helped']} | "
    questions = user['questions_that_could_use_some_love']
    question_strings = []
    for i in range(len(questions)):
      question = questions[i]
      num_replies = len(question.replies)
      question_strings.append(f"[{num_replies} replies]({question.permalink})")
    summary += ", ".join(question_strings)
  return summary

def get_human_readable_time(num_seconds):
  if num_seconds <= 60:
    return f"{num_seconds} seconds"
  num_minutes = round(num_seconds / 60)
  return f"{num_minutes} minute" if num_minutes == 1 else f"{num_minutes} minutes"