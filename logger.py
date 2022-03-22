import inspect
import datetime

"""Args object that returns None for attributes that are not found."""
class Args(object):
  def __getattr__(self, item):
      return None

"""Conditionally prints a message to the terminal.

Message will be printed if either:
- If args.debug = True
- condition = True
"""
def log(message, args = Args(), condition = False):
  if args.debug or condition:
    callerframerecord = inspect.stack()[1]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    time = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    post_info = get_post_info(args)
    print(f"[{time}]{post_info}[{info.filename}][{info.function}:{info.lineno}] {message}")

def get_post_info(args):
  if args.post_id:
    return f"[{args.post_id}]"
  elif args.subreddit and args.post_regex:
    return f"[{args.subreddit}?regex={args.post_regex}]"
  # Unexpected.
  return ""