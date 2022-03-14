import sys
try:
	import praw
except:
	print("praw not installed")
	install_command = sys.executable + " -m pip install praw"
	print("Install command: " + install_command)
	sys.exit()

version = '0.1'

username = 'Encanto_LyricBot'
owner = "00PT"
test_subreddit = '00PTBotTest'
reddit = praw.Reddit('bot1')

def get_comment(comment_id):
	comment = reddit.comment(id=comment_id)
	return comment

def get_comments(subreddit, limit=1000):
	comments = list(subreddit.comments(limit=limit))
	return comments

def get_submission(submission_id):
	submission = reddit.submission(id=submission_id)
	return submission

def get_submissions(subreddit, limit=1000):
	submissions = list(subreddit.new(limit=limit))
	return submissions

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
	comment.refresh()
	replies = list(comment.replies)
	for reply in replies:
		if reply.author:
			if reply.author.name == username:
				return True
			elif (not require_root) and did_reply_comment(reply, username, False):
				return True

	return False

def did_reply_submission(submission, username=username, require_root=True):
	comments = list(submission.comments)
	for comment in comments:
		if comment.author:
			if comment.author.name == username:
				return True
			elif (not require_root) and did_reply_comment(comment, username, False):
				return True
	return False

def get_notifications(type='comment', unread=False, mark_read=True):
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
				if mark_read:
					reddit.inbox.mark_read([notification])
		elif type == 'submission':
			if isinstance(notification, praw.models.Submission):
				result.append(notification)
				if mark_read:
					reddit.inbox.mark_read([notification])
		elif type == 'message':
			if isinstance(notification, praw.models.Message):
				result.append(notification)
				if mark_read:
					reddit.inbox.mark_read([notification])
		elif type == 'all':
			result.append(notification)
			if mark_read:
				reddit.inbox.mark_read([notification])
		elif type == 'mention':
			for mention in reddit.inbox.mentions():
				result.append(mention)
				if mark_read:
					reddit.inbox.mark_read([mention])
		else:
			raise Exception('Invalid notification type: ' + type)

	return list(result)

def reply_to_comment(comment, text):
	comment.reply(text)

def reply_to_submission(submission, text):
	submission.reply(text)

def reply_to_message(message, text):
	message.reply(text)

def get_comment_level(comment):
	level = 0
	parent = comment
	while not is_root_comment(parent):
		level += 1
		parent = parent.parent()
	return level