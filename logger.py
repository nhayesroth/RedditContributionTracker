import inspect
import time

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
    # Get caller info 
    callerframerecord = inspect.stack()[1]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)

    print(f"[{time.ctime(time.time())}][{info.filename}:{info.lineno} - {info.function}] - {message}")