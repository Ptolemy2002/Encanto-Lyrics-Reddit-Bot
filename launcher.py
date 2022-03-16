
import os
import sys
import time

print("Attempting launch on " + time.strftime("%Y-%m-%d %H:%M:%S") + "...")

#get the path of this file
path = os.path.dirname(os.path.realpath(__file__))

def get_file_contents(file_name):
	result = []
	with open(path + "/" + file_name, 'r') as f:
		for line in f:
			line = line.strip()
			if not line.startswith('#'):
				result.append(line)
	return result

def get_songs():
	#Determine if the file "songs.txt" exists. Make it if not.
	if not os.path.exists('songs.txt'):
		with open('songs.txt', 'w') as f:
			pass

	result = []

	for line in get_file_contents('songs.txt'):
		if line != "" and not line.startswith('#'):
			words = line.split(' ')
			result.append(words[0])
	
	return result

def get_subreddits():
	#Determine if the file "subreddits.txt" exists. Make it if not.
	if not os.path.exists('subreddits.txt'):
		with open('subreddits.txt', 'w') as f:
			pass

	result = []

	for line in get_file_contents('subreddits.txt'):
		if line != "" and not line.startswith('#'):
			result.append(line)
	
	return result

songs = get_songs()
subreddits = get_subreddits()
comment_limit = 1000
max_age_hours = 2

launch_count = 0
launch_tries = 0

for song in songs:
	for subreddit in subreddits:
		command = f"{sys.executable} \"{path}/main.py\" {subreddit} {song} {comment_limit} {max_age_hours}"
		print("")
		print("Launching for song '" + song + "' in '" + subreddit + "' subreddit with command:'" + command + "'")
		print("")
		try:
			os.system(command)
			launch_count += 1
		except:
			print("")
			print("Error running bot")
		
		launch_tries += 1
	
	print("")

print("Successfully launched the bot " + str(launch_count) + " times out of " + str(launch_tries) + " tries (" + str(round(launch_count / launch_tries * 100, 2)) + "% success rate).")