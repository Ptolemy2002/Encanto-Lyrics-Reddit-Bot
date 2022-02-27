import sys
import praw
try:
	import praw
except:
	print("praw not installed")
	install_command = sys.executable + " -m pip install praw"
	print("Install command: " + install_command)
	exit()

username = '00PT_TestBot'
test_subreddit = '00PTBotTest'
reddit = praw.Reddit('bot1')

comment_cache = {}
submission_cache = {}

def get_comment(comment_id):
	if comment_id in comment_cache:
		return comment_cache[comment_id]
	else:
		comment = reddit.comment(id=comment_id)
		comment_cache[comment_id] = comment
		return comment

def get_comments(subreddit, limit=1000):
	comments = subreddit.comments(limit=limit)
	result = []
	for comment in comments:
		comment_cache[comment.id] = comment
		result.append(comment)
	return result

def get_submission(submission_id):
	if submission_id in submission_cache:
		return submission_cache[submission_id]
	else:
		submission = reddit.submission(id=submission_id)
		submission_cache[submission_id] = submission
		return submission

def get_submissions(subreddit, limit=1000):
	submissions = subreddit.submissions(limit=limit)
	result = []
	for submission in submissions:
		submission_cache[submission.id] = submission
		result.append(submission)
	return result

def did_reply_comment(comment, username=username, require_root=True):
	replies = comment.replies
	for reply in replies:
		if reply.author.name == username:
			return True
		elif (not require_root) and did_reply_comment(reply, username, False):
			return True
	return False

def did_reply_submission(submission, username=username, require_root=True):
	comments = submission.comments
	for comment in comments:
		if comment.author.name == username:
			return True
		elif (not require_root) and did_reply_comment(comment, username, False):
			return True
	return False