import reddit_tools
from reddit_tools import praw
import os
import tools
import re
import time
import sys

file_contents_cache = {}

def get_file_contents(file_name):
	if not file_name in file_contents_cache:
		result = []
		with open(file_name, 'r') as f:
			for line in f:
				result.append(line.strip())
		file_contents_cache[file_name] = result
		return result
	else:
		return file_contents_cache[file_name]

def clean_up_text(text):
	#Strip accents
	text = tools.strip_accents(text)
	#Remove all non-alphanumeric characters (except - and ') by replacing with space
	text = re.sub(r'[^a-zA-Z0-9\-\']', ' ', text)
	#Replace ' with nothing
	text = re.sub(r'\'', '', text)
	#Replace one or more dashes with a single space
	text = re.sub(r'\-+', ' ', text)
	#Replace all whitespace with a single space
	text = re.sub(r'\s+', ' ', text)
	#Strip leading and trailing spaces
	text = text.strip()
	#Convert to lowercase
	text = text.lower()

	return text

def get_original_lyrics(song):
	#Determine if the directory lyrics/original exists. Make it if not.
	if not os.path.exists('lyrics/original'):
		os.makedirs('lyrics/original')
	
	#Get the file name
	file_name = 'lyrics/original/' + song + '.txt'

	#If the file already exists, return the contents
	if os.path.exists(file_name):
		print("Getting original lyrics for '" + song + "'")
		return get_file_contents(file_name)
	else:
		raise Exception(
			'No lyrics found for "' + song + 
			'". Please add them through a text file in the lyrics/original directory. The file name should be the same as the song name.'
		)

def get_clean_lyrics(song):
	#Determine if the directory lyrics/clean exists. Make it if not.
	if not os.path.exists('lyrics/clean'):
		os.makedirs('lyrics/clean')
	
	#Get the file name
	file_name = 'lyrics/clean/' + song + '.txt'
	#Get the file name of the original lyrics
	original_file_name = 'lyrics/original/' + song + '.txt'

	#If the file already exists, return the contents
	if os.path.exists(file_name):
		print("Getting clean lyrics for '" + song + "'")
		return get_file_contents(file_name)
	elif os.path.exists(original_file_name):
		#get the file contents of the original lyrics and clean each line individually
		lyrics = get_original_lyrics(song)
		print("Ganerating clean lyrics for '" + song + "'")
		clean_lyrics = []
		for line in lyrics:
			clean_lyrics.append(clean_up_text(line))
		
		#Write the cleaned lyrics to the file
		with open(file_name, 'w') as f:
			for line in clean_lyrics:
				f.write(line + '\n')
		return clean_lyrics
	else:
		raise Exception(
			'No lyrics found for "' + song + 
			'". Please add them through a text file in the lyrics/original directory. The file name should be the same as the song name.'
		)

def get_user_blacklist():
	user_blacklist = []
	if os.path.exists('user_blacklist.txt'):
		user_blacklist = get_file_contents('user_blacklist.txt')
	else:
		#Write an empty blacklist to the file
		with open('user_blacklist.txt', 'w') as f:
			pass
	return user_blacklist

def update_user_blacklist(user_blacklist):
	#overwrite the user blacklist with the new one
	with open('user_blacklist.txt', 'w') as f:
		for user in user_blacklist:
			f.write(user + '\n')

def strip_lines(string):
	#Strip leading and trailing whitespace
	string = string.strip()
	lines = string.split('\n')
	#Strip leading and trailing whitespace from each line
	for i in range(len(lines)):
		lines[i] = lines[i].strip()
	return "\n".join(lines)

def get_songs():
	#Determine if the file "songs.txt" exists. Make it if not.
	if not os.path.exists('songs.txt'):
		with open('songs.txt', 'w') as f:
			pass

	result = {}
	result["list"] = []
	result["dict"] = {}

	for line in get_file_contents('songs.txt'):
		if line != "":
			words = line.split(' ')
			result["list"].append(words[0])
			result["dict"][words[0]] = strip_lines(" ".join(words[1:]))
	
	return result

songs = get_songs()
song_list = songs["list"]
song_friendly_names = songs["dict"]

args = tools.get_args(
	[
		{
			'name': 'subreddit',
			'target_type': str,
			'input_args': {
				'invalid_message': 'Subreddit cannot be empty and must only contain letters, numbers, and underscores. Use "default" to use the test subreddit.',
				'cancel': 'default'
			},
			'condition': lambda x: x != '' and re.match(r'^[a-zA-Z0-9_]+$', x) is not None,
			'default': reddit_tools.test_subreddit
		},
		{
			'name': 'song',
			'target_type': lambda x : clean_up_text(x) if type(x) is str else None,
			'input_args': {
				'invalid_message': 'Song must be within the list of songs as specified in the songs.txt file.'
			},
			'condition': lambda x: x in song_list,
			'raise': True
		},

		{
			'name': 'comment limit',
			'target_type': int,
			'input_args': {
				'invalid_message': 'Comment limit must be a positive integer.',
				'cancel': 'default'
			},
			'condition': lambda x: x > 0,
			'default': 1000,
		},

		{
			'name': 'max age (hours)',
			'target_type': float,
			'input_args': {
				'invalid_message': 'Max age must be a positive number.',
				'cancel': 'default'
			},
			'condition': lambda x: x > 0,
			'default': 24.0,
		}
	], False)

print("Specified subreddit: " + args['subreddit'])
print("Specified song: " + args['song'])

subreddit = reddit_tools.reddit.subreddit(args['subreddit'])
song_name = args['song']
comment_limit = args['comment limit']
max_age_hours = args['max age (hours)']

default_reply = strip_lines(
	"""	
		<next_line>

		---

		**I am a bot.** I have responded to this comment chain with the next lyric to the Encanto song "<friendly_song_name>"
		according to my best estimate of the current position.

		If you have any questions or suggestions, please contact u/<owner> via private message.

		You may reply with "<opt_out_text>" to opt out of this service.

		Alternatively, you may send a private message to u/<username> with "<opt_out_text>" as the subject to do the same thing.

		If you would ever like to opt in again, either reply to <username>'s comments with "<opt_in_text>"
		or send a private message to u/<username> with "<opt_in_text>" as the subject.

		My source code is available [here](<source_link>).

		---

		Current position: <current_position>
		Internal song name: <internal_song_name>
	"""
)

print("Getting subreddit moderators")
mods = reddit_tools.get_mods(subreddit)

print("Getting user blacklist")
user_blacklist = get_user_blacklist()

print("checking for user blacklist additions")
opt_in_text = "!optin"
opt_out_text = "!optout"

#search for comments
for comment in reddit_tools.get_notifications("comment", True):
	body = comment.body
	user = comment.author.name
	if body.lower() == opt_out_text.lower() and not user in user_blacklist:
		user_blacklist.append(user)
		update_user_blacklist(user_blacklist)
		print("User " + user + " has opted out of notifications.")
		reddit_tools.reply_to_comment(comment, "You have opted out of this bot's services. Have a nice day!")
	elif body.lower() == opt_in_text.lower() and user in user_blacklist:
		user_blacklist.remove(user)
		update_user_blacklist(user_blacklist)
		print("User " + user + " has opted in to notifications.")
		reddit_tools.reply_to_comment(comment, "You have opted back in to this bot's services. Have a nice day!")

#search for messages
for message in reddit_tools.get_notifications("message", True):
	body = message.subject
	user = message.author.name
	if body.lower() == opt_out_text.lower() and not user in user_blacklist:
		user_blacklist.append(user)
		update_user_blacklist(user_blacklist)
		print("User " + user + " has opted out of notifications.")
		reddit_tools.reply_to_message(message, "You have opted out of this bot's services. Have a nice day!")
	elif body.lower() == opt_in_text.lower() and user in user_blacklist:
		user_blacklist.remove(user)
		update_user_blacklist(user_blacklist)
		print("User " + user + " has opted in to notifications.")
		reddit_tools.reply_to_message(message, "You have opted back in to this bot's services. Have a nice day!")


original_lyrics = get_original_lyrics(song_name)
clean_lyrics = get_clean_lyrics(song_name)

#Get a list of comments in the subreddit. Time how long this takes.
print("Getting comments")
start_time = time.time()
comments = reddit_tools.get_comments(subreddit, comment_limit)
total_comments = len(comments)
handled_comments = 0
print(f"Got {total_comments} comments in {str(time.time() - start_time)} seconds")

#Loop through the comments. Time how long this takes.
print("Handling comments")
start_time = time.time()
for comment in comments:
	#Don't handle the comment if it's too old
	if comment.created_utc < time.time() - max_age_hours * 3600:
		print(f"Found comment {comment.id} that is too old. Skipping.")
		continue

	#Don't handle the comment if it is a root comment made by a moderator
	if comment.author.name in mods and reddit_tools.is_root_comment(comment):
		print(f"Found root comment '{comment.id}' made by a moderator. Skipping...")
		continue

	#Don't handle the comment if it is  made by a blacklisted user
	if comment.author.name in user_blacklist:
		print(f"Found comment '{comment.id}' made by a blacklisted user (u/{comment.author}). Skipping...")
		continue

	#Don't handle the comment if it's made by the bot
	if comment.author.name == reddit_tools.username:
		print(f"Found comment '{comment.id}' by this bot. Skipping...")
		continue

	#Don't handle the comment if we have already replied to a comment further down the chain
	if reddit_tools.did_reply_comment(comment, require_root=False):
		print(f"Found comment '{comment.id}' already replied to. Skipping...")
		continue
	
	#print(f"Found comment '{comment.id}' by '{comment.author.name}'. Body:")
	formatted_body = clean_up_text(comment.body)
	#print(f"\t{formatted_body}")
	handled_comments += 1

ignored_comments = total_comments - handled_comments
print(f"Handled {handled_comments} out of {total_comments} ({ignored_comments} ignored; {(handled_comments/total_comments) * 100}% coverage) comments in {str(time.time() - start_time)} seconds")
