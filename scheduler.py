import sys
import time
import traceback

"""Executes the specified task every interval=delay seconds."""
def every(delay, task, task_args):
  next_time = time.time() + delay
  while True:
    time_to_sleep = max(0, next_time - time.time())
    time.sleep(time_to_sleep)
    try:
      print(f"\nstarting task execution at: {time.ctime(time.time())}...\n")
      task(task_args)
    except Exception:
      traceback.print_exc()
      raise
    # skip tasks if we are behind schedule:
    next_time += (time.time() - next_time) // delay * delay + delay