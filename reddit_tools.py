import sys
import praw
try:
	import praw
except:
	print("praw not installed")
	install_command = sys.executable + " -m pip install praw"
	print("Install command: " + install_command)
	exit()

version = '0.1'

username = '00PT_TestBot'
owner = "00PT"
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
	submissions = subreddit.new(limit=limit)
	result = []
	for submission in submissions:
		submission_cache[submission.id] = submission
		result.append(submission)
	return result

def get_mods(subreddit):
	mods = subreddit.moderator()
	result = []
	for mod in mods:
		result.append(mod.name)
	return result

def is_root_comment(comment):
	if comment.parent_id == comment.link_id:
		return True
	else:
		return False

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

def get_notifications(type='comment', unread=False):
	notifications = []
	if unread:
		notifications = reddit.inbox.unread()
	else:
		notifications = reddit.inbox.all()
	
	result = []
	for notification in notifications:
		if type == 'comment':
			if isinstance(notification, praw.models.Comment):
				result.append(notification)
				reddit.inbox.mark_read([notification])
		elif type == 'submission':
			if isinstance(notification, praw.models.Submission):
				result.append(notification)
				reddit.inbox.mark_read([notification])
		elif type == 'message':
			if isinstance(notification, praw.models.Message):
				result.append(notification)
				reddit.inbox.mark_read([notification])
		elif type == 'all':
			result.append(notification)
			reddit.inbox.mark_read([notification])
		else:
			raise Exception('Invalid notification type: ' + type)

	return result

def reply_to_comment(comment, text):
	comment.reply(text)

def reply_to_submission(submission, text):
	submission.reply(text)

def reply_to_message(message, text):
	message.reply(text)
