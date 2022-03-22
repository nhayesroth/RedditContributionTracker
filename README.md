# RedditContributionTracker

## Summary
Python script for a reddit bot that does the following:
- Scans one or more reddit threads for user contributions (top-level comments and replies to top-level comments)
- Sorts the results to determine:
  - The most helpful users (measured by the number of replies they've made to other top-level comments) 
  - The most helpful users who have not received replies to their own top-level comments
- Replies to the thread with the results

## Instructions
- Configure the bot using environment variables for your use case (see full ist of options below).
```bash
# On local machine
export comment_mode='edit'
export posts='[ { "subreddit":"abc", "post_regex":"Hello world" }, { "subreddit":"Zebra", "post_regex":"Fancy thread title" } ]'

# On Heroku
heroku config:set client_id=foobar
heroku config:set client_secret=zebra
```
- Run the bot (optionally supplying command-line arguments, which override your environment variables):
```
$ python3 main.py --debug True --reply_threshold 5
```

## Configuration

### Configure your bot
- `client_id`: The ID of your bot (see [bot_creds_example.png](bot_creds_example.png)).
- `client_secret`: The secret of your bot (see [bot_creds_example.png](bot_creds_example.png)).
- `user_agent`: User agent passed to PRAW (likely the name of your bot or a description of the specific application).
- `username`: The username of your bot's reddit account.
- `password`: The password for your bot's account.

### Configure which post your bot scans
- `posts`: A JSON string that describes one or more threads that the bot will operate on. Can be a single object describing 1 thread, or a list of objects describing multiple threads. Meaningful attributes are:
  - `subreddit`: The subreddit the bot will search for the the thread matching `post_regex`.
  - `post_regex`: A python regex to match the reddit post your bot will scan.
  - `post_id`: Choose a specific post to scan (instead of using the `subreddit` and `post_regex`).
  - Examples:
  ```
  export posts='[{ "subreddit": "pics", "post_regex": "Discussion thread" }, { "subreddit": "politics", "post_regex": "Daily chat" }]'
  export posts='[{ "post_id": "abc123" }]'
  export posts='{ "post_id": "foobar" }'
  ```

### Configure how the bot processes the target post
- `reply_threshold`: The minimum number of replies to a top-level comment before the bot will stop including it in the results.

### Configure the bot's final output
- `comment_mode`: Either `new`, which will delete the bot's previous comment and post a new one, or `edit`, which will edit the bot's previous comment.
- `interval`: The interval (in seconds) the bot will wait between scans. Note: this only affects the resulting message that the bot produces. Actual scheduling is handled by the Heroku Scheduler.
- `mode`: Either `print`, which will print results to the command line, or `post`, which will post results as a Reddit comment.


### Debug options:
- `debug`: Prints various debug statements that show the bot's progress.
- `answer_username`: Only include answers from 1 user.
- `question_username`: Only include questions from 1 user.
- `print_answers`: Prints scanned answers on the command-line.
- `print_questions`: Prints scanned questions on the command-line.


## How?

### How does it interact with Reddit?
The script uses [PRAW](https://praw.readthedocs.io/en/latest/index.html) to interact with reddit's API.

### How does it run periodically?
The script relies on [Heroku Scheduler](https://devcenter.heroku.com/articles/scheduler) to run the script every 10 minutes.

### How does it determine who the most helpful users are?
More replies to top-level comments => more helpful.

### How does it determine which questions "could use some love"?
Any question with fewer than `reply_threshold` replies could use some love.