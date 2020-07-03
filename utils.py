import re

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