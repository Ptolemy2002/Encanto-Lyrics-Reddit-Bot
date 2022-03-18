from operator import truediv
import reddit_tools
import os
import sys
import tools
import re
import time
import math

file_contents_cache = {}

def get_file_contents(file_name):
	if not file_name in file_contents_cache:
		result = []
		with open(file_name, 'r') as f:
			for line in f:
				line = line.strip()
				if not line.startswith('#'):
					result.append(line)
		file_contents_cache[file_name] = result
		return result
	else:
		return file_contents_cache[file_name]

def clean_up_text(text):
	#Strip accents
	text = tools.strip_accents(text)
	#Remove all non-alphanumeric characters (except - and ') by replacing with space
	text = re.sub(r'[^a-zA-Z0-9\-\'’]', ' ', text)
	#Replace ' with nothing
	text = re.sub(r'[\'’]', '', text)
	#Replace one or more dashes with a single space
	text = re.sub(r'\-+', ' ', text)
	#Replace all whitespace with a single space
	text = re.sub(r'\s+', ' ', text)
	#Strip leading and trailing spaces
	text = text.strip()
	#Convert to lowercase
	text = text.lower()
	#Replace a character repeated more than once with a single instance
	text = re.sub(r'(.)\1+', r'\1', text)

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
			line = line.strip()
			if not line.startswith('#'):
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
		if line != "" and not line.startswith('#'):
			words = line.split(' ')
			result["list"].append(words[0])
			result["dict"][words[0]] = strip_lines(" ".join(words[1:]))
	
	return result

def close_match(lyric, text, max_missed_words=3):
	text = clean_up_text(text)

	#Break both strings into words
	lyric_words = lyric.split(' ')
	text_words = text.split(' ')
	if len(text_words) < max_missed_words:
		return lyric == text

	#If the length of the two strings is not within the range, return false
	if abs(len(lyric_words) - len(text_words)) > max_missed_words:
		return False
	
	#Loop through the words of the longer string and check if they are in the same order
	longest_words = []
	shortest_words = []
	if len(lyric_words) > len(text_words):
		longest_words = lyric_words
		shortest_words = text_words
	else:
		longest_words = text_words
		shortest_words = lyric_words

	missed_words = 0
	for i in range(len(longest_words)):
		if i > len(shortest_words) - 1 or longest_words[i] != shortest_words[i]:
			missed_words += 1
			if missed_words > max_missed_words:
				return False
	return True

def get_potential_lyric_indexes(song, lyric):
	result = []
	clean_lyric = clean_up_text(lyric)
	for i in range(len(song)):
		line = song[i]
		if close_match(line, clean_lyric):
			result.append(i)
	return result

def get_lyric_extent(song, song_name, comment, index, username):
	current_comment = comment
	current_index = index
	current_extent = 0
	while current_index >= 0:
		if current_comment.author.name == username:
			#find the current position using regex "Current position: <current_position>"
			current_position = re.search(r'Current position: (\d+)', current_comment.body)
			if current_position is None:
				print("Found one of this bot's comments, but it doesn't have a current position. This marks the end of the previous chain.")
				return current_extent - 1
			else:
				current_position = int(current_position.group(1))
				if current_position == current_index:
					#find the internal song name using regex "Internal song name: <internal_song_name>"
					internal_song_name = re.search(r'Internal song name: (\w+)', current_comment.body)
					if internal_song_name is None:
						print("Found one of this bot's comments, but it doesn't have an internal song name. This marks the end of the previous chain.")
						return current_extent - 1
					elif internal_song_name.group(1) == song_name:
						#As we have guaranteed that this comment is the one that matches the chain, we return infinity so that it will be recognized as the highest extent
						return math.inf
					else:
						print("Found one of this bot's comments, but it doesn't have the same internal song name as was specified. This marks the end of the previous chain.")
						return current_extent - 1			
				else:
					print("Found one of this bot's comments, but the position was not the same as was expected. This marks the end of the previous chain.")
					return current_extent - 1

		if close_match(song[current_index], current_comment.body):
			current_extent += 1
		else:
			return current_extent

		if reddit_tools.is_root_comment(current_comment):
			break

		current_comment = current_comment.parent()
		current_index -= 1
	
	return current_extent

def get_lyric_index(song, song_name, comment, username, potential_indexes=None):
	if not potential_indexes:
		potential_indexes = get_potential_lyric_indexes(song, comment.body)

	if len(potential_indexes) == 0:
		return None
	elif len(potential_indexes) == 1:
		return potential_indexes[0]
	else:
		extent_array = []
		max_extent = 0
		for index in potential_indexes:
			extent = get_lyric_extent(song, song_name, comment, index, username)
			if extent is not None:
				extent_array.append({"extent": extent, "index": index})
				if extent > max_extent:
					max_extent = extent

		#sort extent_array by index lowest to highest
		extent_array.sort(key=lambda x: x["index"])

		#return the index of the first element with the maximum extent
		for i in range(len(extent_array)):
			if extent_array[i]["extent"] == max_extent:
				return extent_array[i]["index"]

def is_bottom_chain(song, comment):
	comment.refresh()
	if comment.replies is None:
		return True
	else:
		for reply in comment.replies:
			potential_indexes = get_potential_lyric_indexes(song, clean_up_text(reply.body))
			if len(potential_indexes) > 0:
				return False
		return True


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
			'target_type': str,
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

		For more information (including how to report a bug or opt out), click [here](<help_link>).

		---

		Current position: <current_position>

		Internal song name: <internal_song_name>
	"""
)

end_reply = strip_lines(
	"""
		That's all the lyrics I have for the song "<friendly_song_name>".

		---

		**I am a bot.** This comment chain was for the Encanto song "<friendly_song_name>".

		For more information (including how to report a bug or opt out), click [here](<help_link>).

		---

		Current position: <current_position>

		Internal song name: <internal_song_name>
	"""
)
help_link = "https://www.reddit.com/r/Encanto_LyricBot/comments/tesdvp/encanto_lyric_bot_faq/"

def format_reply(next_line, current_position, internal_song_name, friendly_song_name, help_link, owner, username, reply_base=default_reply):
	reply = reply_base.replace('<next_line>', next_line)
	reply = reply.replace('<current_position>', str(current_position))
	reply = reply.replace('<internal_song_name>', internal_song_name)
	reply = reply.replace('<friendly_song_name>', friendly_song_name)
	reply = reply.replace('<help_link>', help_link)
	reply = reply.replace('<owner>', owner)
	reply = reply.replace('<username>', username)
	return reply
	

"""print("Getting subreddit moderators")
mods = reddit_tools.get_mods(subreddit)"""

print("Getting user blacklist")
user_blacklist = get_user_blacklist()

print("checking for user blacklist additions")
opt_in_text = "!optin"
opt_out_text = "!optout"

#search for comments
for comment in reddit_tools.get_notifications("comment", True):
	if comment.author:
		body = comment.body
		user = comment.author.name
		if body.lower() == opt_out_text.lower() and not user in user_blacklist:
			user_blacklist.append(user)
			print("User " + user + " has opted out of notifications.")
			reddit_tools.reply_to_comment(comment, "You have opted out of this bot's services. Have a nice day!")
		elif body.lower() == opt_in_text.lower() and user in user_blacklist:
			user_blacklist.remove(user)
			print("User " + user + " has opted in to notifications.")
			reddit_tools.reply_to_comment(comment, "You have opted back in to this bot's services. Have a nice day!")

#search for messages
for message in reddit_tools.get_notifications("message", True):
	if message.author:
		body = message.subject
		user = message.author.name
		if body.lower() == opt_out_text.lower() and not user in user_blacklist:
			user_blacklist.append(user)
			print("User " + user + " has opted out of notifications.")
			reddit_tools.reply_to_message(message, "You have opted out of this bot's services. Have a nice day!")
		elif body.lower() == opt_in_text.lower() and user in user_blacklist:
			user_blacklist.remove(user)
			print("User " + user + " has opted in to notifications.")
			reddit_tools.reply_to_message(message, "You have opted back in to this bot's services. Have a nice day!")

update_user_blacklist(user_blacklist)

requests_used = reddit_tools.reddit.auth.limits['used']

original_lyrics = get_original_lyrics(song_name)
clean_lyrics = get_clean_lyrics(song_name)

ignore_indexes = []
for i in range(len(original_lyrics)):
	if original_lyrics[i][0] == "^":
		ignore_indexes.append(i)
		original_lyrics[i] = original_lyrics[i][1:]

#Get a list of comments in the subreddit. Time how long this takes.
print("Getting comments")
start_time = time.time()
comments = reddit_tools.get_comments(subreddit, comment_limit)
#sort comments by age (newest first)
comments = sorted(comments, key=lambda x: x.created_utc, reverse=True)
total_comments = len(comments)

if total_comments == 0:
	print("No comments found.")
	sys.exit()

handled_comments = 0
replied_comments = 0
print(f"Got {total_comments} comments in {str(time.time() - start_time)} seconds")

#Loop through the comments. Time how long this takes.
print("Handling comments")
start_time = time.time()
for comment in comments:
	if comment.author:
		age = (time.time() - comment.created_utc) / 3600
		#Don't handle the comment if it's too old
		if age > max_age_hours:
			print(f"Found comment '{comment.id}' that is too old ({age} hours). Stopping here...")
			#Stop processing additional comments, since all the rest are going to be too old
			break

		"""#Don't handle the comment if it is a root comment made by a moderator
		if comment.author.name in mods and reddit_tools.is_root_comment(comment):
			print(f"Found root comment '{comment.id}' made by a moderator. Skipping...")
			continue"""

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

		print("Found comment '" + comment.id + "' by '" + comment.author.name + "' that could be a match.")
		print("Formatted Text: " + formatted_body)
		potential_indexes = get_potential_lyric_indexes(clean_lyrics, formatted_body)
		if len(potential_indexes) > 0:
			if is_bottom_chain(clean_lyrics, comment):
				current_position = get_lyric_index(clean_lyrics, song_name, comment, reddit_tools.username, potential_indexes=potential_indexes)
				if current_position == None:
					print(f"No match found. Skipping...")
					handled_comments += 1
					continue
				else:
					#current_position += 1
					print(f"Match Position: {current_position}")
					extent = get_lyric_extent(clean_lyrics, song_name, comment, current_position, reddit_tools.username)
					
					if current_position + 1 != len(clean_lyrics) or extent > 1:
						if current_position in ignore_indexes and extent == 1:
							print("Found a match, but it's an ignored lyric and at the beginning of a chain.")
							print("We don't start chains with ignored lyrics. Skipping...")
							handled_comments += 1
							continue
						
						if current_position == len(clean_lyrics) - 1:
							print(f"Found match at the end of the song.")
							print("replying to indicate this...")
							reply = format_reply(original_lyrics[current_position], current_position, song_name, song_friendly_names[song_name], help_link, reddit_tools.owner, reddit_tools.username, reply_base=end_reply)
							reddit_tools.reply_to_comment(comment, reply)
							handled_comments += 1
							continue
						
						print("replying...")
						next_line = original_lyrics[current_position + 1]
						reply = format_reply(next_line, current_position + 1, song_name, song_friendly_names[song_name], help_link, reddit_tools.owner, reddit_tools.username)
						reddit_tools.reply_to_comment(comment, reply)
						if (current_position + 1) == len(clean_lyrics) - 1:
							print(f"Just replied with the last line of the song.")
							print("replying to indicate this...")
							reply = format_reply(original_lyrics[current_position + 1], current_position + 1, song_name, song_friendly_names[song_name], help_link, reddit_tools.owner, reddit_tools.username, reply_base=end_reply)
							reddit_tools.reply_to_comment(comment, reply)
						replied_comments += 1
					else:
						print("Not replying because the next line is the last line of the song and there is no evidence of a preexisting chain.")

					handled_comments += 1
					
			else:
				print(f"This comment is not at the bottom of the chain. Skipping...")
				handled_comments += 1
				continue
		else:
			print(f"This comment doesn't seem to match any lyrics. Skipping...")
			handled_comments += 1
	else:
		print(f"Found comment '{comment.id}' that does not have an author. Skipping...")


limit_info = reddit_tools.reddit.auth.limits
print(f"limit info: {limit_info}")
seconds_until_reset = (limit_info['reset_timestamp'] - time.time())
#split into minutes and seconds
minutes = int(math.floor(seconds_until_reset / 60))
seconds = str(int(round(seconds_until_reset % 60)))
if len(seconds) == 1:
	seconds = "0" + seconds
print(f"Approximate time until reset (upper bound): {minutes}:{seconds}")

ignored_comments = total_comments - handled_comments
print(f"Handled {handled_comments} out of {total_comments} ({ignored_comments} ignored; {replied_comments} replied to; {(handled_comments/total_comments) * 100}% coverage) comments in {str(time.time() - start_time)} seconds")
print(f"Used a total of {limit_info['used'] - requests_used} requests in this instance of the script.")