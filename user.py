import utils

class User:
    """Represents a user participating in the daily thread."""
    def __init__(self, name, questions=[], replies=[], num_replies_to_questions=0):
        self.name = name
        self.questions = questions
        self.replies = replies
        self.num_replies_to_questions = num_replies_to_questions

    def __str__(self):
        string = f"""{self.name}: relative_contribution={self.relative_contribution()}
        \t+num_replies={len(self.replies)} 
        \t-num_replies_to_questions={self.num_replies_to_questions} 
        \t-num_questions={len(self.questions)}"""
        for summary in self._question_summaries():
            string += f"\n\t\tQuestion: {summary}"
        for summary in self._reply_summaries():
            string += f"\n\t\tReply: {summary}"
        return string

    @classmethod
    def combine(cls, user1, user2):
        if user1.name != user2.name:
            print(f"User1.name({user1.name}) is not equal to User2.name({user2.name})!!!!")
        return cls(
            name = user1.name,
            questions = user1.questions + user2.questions,
            replies = user1.replies + user2.replies,
            num_replies_to_questions = user1.num_replies_to_questions + user2.num_replies_to_questions)

    def add_question(self, comment):
        self.questions.append(comment)

    def get_profile_link_string(self):
        return f"[{self.name}](https://reddit.com/user/{self.name}/)"

    def _question_summaries(self):
        summaries = []
        for question in self.questions:
            summaries.append(utils.get_abbreviated_comment(question))
        return summaries

    def add_reply(self, comment):
        self.replies.append(comment)

    def reply_summaries(self):
        summaries = []
        for reply in self.replies:
            summaries.append(utils.get_abbreviated_comment(reply))
        return summaries

    def num_replies(self):
        return len(self.replies)

    def inc_num_replies_to_questions(self):
        self.num_replies_to_questions += 1

    def relative_contribution(self):
        return len(self.replies) - self.num_replies_to_questions - len(self.questions)

    def relative_contribution_summary(self):
        return f"{self.relative_contribution()} = numReplies[{len(self.replies)}] - numRepliesToQuestions[{self.num_replies_to_questions}] - numQuestions[{len(self.questions)}]"
