import sys
import time
import traceback

"""Executes the specified task every interval=delay seconds."""
def every(delay, task):
  next_time = time.time() + delay
  while True:
    time_to_sleep = max(0, next_time - time.time())
    time.sleep(time_to_sleep)
    try:
      task()
    except Exception:
      traceback.print_exc()
    # skip tasks if we are behind schedule:
    next_time += (time.time() - next_time) // delay * delay + delay