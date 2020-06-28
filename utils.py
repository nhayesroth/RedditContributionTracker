import re

"""Returns the first 20 chars of a comment with whitespaces replaced by single-space chars."""
def get_abbreviated_comment(comment):
    return re.sub(r"\s+", " ", comment.body[0 : 20], flags=re.UNICODE)