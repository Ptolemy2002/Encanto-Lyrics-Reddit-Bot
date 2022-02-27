import reddit_tools
from reddit_tools import praw
import os
import tools
import re
import time

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

song_list = get_file_contents('songs.txt')

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
			'name': 'comment_limit',
			'target_type': int,
			'input_args': {
				'invalid_message': 'Comment limit must be a positive integer.',
				'cancel': 'default'
			},
			'condition': lambda x: x > 0,
			'default': 1000,
		}
	], False)

print("Specified subreddit: " + args['subreddit'])
print("Specified song: " + args['song'])

subreddit = reddit_tools.reddit.subreddit(args['subreddit'])
song_name = args['song']
comment_limit = args['comment_limit']

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
	#Don't handle the comment if it's made by the bot
	if comment.author == reddit_tools.username:
		print(f"Found comment '{comment.id}' by this bot. Skipping...")
		continue

	#Don't handle the comment if it has already been replied to
	if reddit_tools.did_reply_comment(comment):
		print(f"Found comment '{comment.id}' already replied to. Skipping...")
		continue
	
	#print(f"Found comment '{comment.id}' by '{comment.author.name}'. Body:")
	formatted_body = clean_up_text(comment.body.replace('\n', '\n\t'))
	#print(f"\t{formatted_body}")
	handled_comments += 1

ignored_comments = total_comments - handled_comments
print(f"Handled {handled_comments} out of {total_comments} ({ignored_comments} ignored; {(handled_comments/handled_comments) * 100}% coverage) comments in {str(time.time() - start_time)} seconds")
