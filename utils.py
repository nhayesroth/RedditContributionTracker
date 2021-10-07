import re
import os
from copy import deepcopy
import time 

"""Returns an abbreviated comment string.

- Includes the first 20 chars of a comment
- Replaces all whitespace characters replaced with single-space chars.
- Appends a link to the comment.
"""
def get_abbreviated_comment(comment):
    return (re.sub(r"\s+", " ", comment.body[0 : 20], flags=re.UNICODE) +
        f" - https://reddit.com{comment.permalink}")

def get_most_helpful_summary(users):
  """Returns a string summary of the most helpful users, formatted for Reddit.

  Only includes the top 10 most helpful users and only incldues users who have
  answered at least 1 question.
  """
  summary = ("User | # Helped"
            "\n----|:-----:|:-----:|")
  for user in users[:10]:
    if user.num_replies() == 0:
      continue;
    else:
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
      question_strings.append(f"[{pluralize_replies(num_replies)}]({question.permalink})")
    summary += ", ".join(question_strings)
  return summary

def pluralize_replies(num_replies):
  if num_replies == 1:
    return "1 reply"
  return f"{num_replies} replies"

def get_human_readable_time(num_seconds):
  if num_seconds <= 60:
    return f"{num_seconds} seconds"
  num_minutes = round(num_seconds / 60)
  return f"{num_minutes} minute" if num_minutes == 1 else f"{num_minutes} minutes"