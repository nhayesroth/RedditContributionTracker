# RedditContributionTracker

## Summary
Python script for a reddit bot that does the following:
- Periodically scans a reddit thread for user contributions (top-level comments and replies to top-level comments)
- Sorts the results to determine:
  - The most helpful users (measured as by the number of replies to top-level comments) 
  - The most helpful users who have not received replies to their own top-level comments
- Replies to the thread with the results (posting a new comment if none exists or editing a preexisting comment if one already exists)

## Instructions
- Fill out [config.ini](https://github.com/nhayesroth/RedditContributionTracker/blob/master/config.ini) with values appropriate for your use case
- Run the bot:
```
$ python3 main.py
```

## Configuration
Options are configured as environment variables. For example:

```bash
# On local machine
export interval=600
export subreddit=DynastyFF
export post_regex='\[Daily - TRADE\]'

# On Heroku
heroku config:set client_id=foobar
heroku config:set client_secret=zebra
```

### Important options:

- `client_id`: The ID of your bot (see [bot_creds_example.png](bot_creds_example.png)).
- `client_secret`: The secret of your bot (see [bot_creds_example.png](bot_creds_example.png)).
- `interval`: The interval (in seconds) the bot will wait between scans.
- `mode`: Either `print`, which will print results to the command line, or `post`, which will post results as a Reddit comment.
- `password`: The password for your bot's account.
- `post_regex`: A python regex to match the reddit post your bot will scan.
- `reply_threshold`: The minimum number of replies to a top-level comment before the bot will stop including it in the results.
- `subreddit`: The subreddit the bot will search for the the thread matching `post_regex`.
- `user_agent`: User agent passed to PRAW (likely the name of your bot or a description of the specific application).
- `username`: The username of your bot's reddit account.


### Debug options:

- `answer_username`: Only include answers from 1 user.
- `post_id`: Choose a specific post to scan (instead of using the `subreddit` and `post_regex`).
- `print_answers`: Prints scanned answers on the command-line.
- `print_questions`: Prints scanned questions on the command-line.
- `question_username`: Only include questions from 1 user.


## How?

### How does it interact with Reddit?
The script uses [PRAW](https://praw.readthedocs.io/en/latest/index.html) to interact with reddit's API.

### How does it run periodically?
The script spawns an independent thread to handle the task of scanning and posting. The thread sleeps for the configured interval before waking up and running the task again. This continues forever, until the the program is killed.

### How does it know which thread to scan?
The script scans "hot" posts in `subreddit` for the first post matching `post_regex` (both configured in [config.ini](https://github.com/nhayesroth/RedditContributionTracker/blob/master/config.ini)).

### How does it determine who the most helpful users are?
More replies to top-level comments => more helpful.

### How does it determine which questions "could use some love"?
Any question with fewer than `reply_threshold` replies could use some love.