
import os
import sys
import time
import main
import traceback
import tools

wait_time = tools.get_args([
	{
		'name': 'wait_time',
		'target_type': float,
		'input_args': {
			'invalid_message': 'Wait time must be a positive number or 0.',
			'cancel': 'default'
		},
		'condition': lambda x: x >= 0,
		'default': 0
	}
], False)['wait_time']

print("Attempting launch on " + time.strftime("%Y-%m-%d %H:%M:%S") + "...")
#store the current time inside "start_time.txt" Overwrite if it exists. Create if it doesn't.
with open('start_time.txt', 'w', encoding="utf-8") as f:
	f.write(str(time.time()))

#get the path of this file
path = os.path.dirname(os.path.realpath(__file__))

def get_file_contents(file_name):
	result = []
	with open(path + "/" + file_name, 'r', encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line.startswith('#'):
				result.append(line)
	return result

def get_songs():
	#Determine if the file "songs.txt" exists. Make it if not.
	if not os.path.exists('songs.txt'):
		with open('songs.txt', 'w', encoding="utf-8") as f:
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
		with open('subreddits.txt', 'w', encoding="utf-8") as f:
			pass

	result = []

	for line in get_file_contents('subreddits.txt'):
		if line != "" and not line.startswith('#'):
			result.append(line)
	
	return result

subreddits = get_subreddits()
comment_limit = 1000
max_age_hours = 2
compatibility_mode = 2

launch_count = 0
launch_tries = 0

for subreddit in subreddits:
	args = {
		"subreddit": subreddit,
		"comment limit": comment_limit,
		"max age (hours)": max_age_hours,
		"compatibility mode": compatibility_mode
	}

	command = f"{sys.executable} \"{path}/main.py\" {subreddit} {comment_limit} {max_age_hours} {compatibility_mode}"
	print("")
	print("Launching in '" + subreddit + "' subreddit")
	print("Command to execute: " + command)
	print("")
	try:
		main.main(args)
		launch_count += 1
	except Exception as e:
		print("")
		print("Error running bot")
		print(traceback.format_exc())
	
	launch_tries += 1

print("")

print("Successfully launched the bot " + str(launch_count) + " times out of " + str(launch_tries) + " tries (" + str(round(launch_count / launch_tries * 100, 2)) + "% success rate).")
#delete the start_time.txt file
os.remove('start_time.txt')

#wait for the specified amount of time before ending the program
if wait_time > 0:
	print("")
	print("Waiting for " + str(wait_time) + " seconds before exiting...")
	time.sleep(wait_time)
	print("-" * 20)