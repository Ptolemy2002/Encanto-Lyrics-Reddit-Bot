import os

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

songs = get_songs()

print("Generating list versions of each song...")
#For each song, write a file in <path>/lyrics/list/<song>.txt with the index (1-based) of the lyric followed by a space and the lyric itself.
for i in range(len(songs)):
	song_contents = get_file_contents("lyrics/original/" + songs[i] + ".txt")
	#create the list file if it doesn't exist
	if not os.path.exists("lyrics/list/" + songs[i] + ".txt"):
		os.makedirs("lyrics/list/", exist_ok=True)
		with open("lyrics/list/" + songs[i] + ".txt", 'w') as f:
			pass

	with open(path + "/lyrics/list/" + songs[i] + ".txt", 'w') as f:
		for j in range(len(song_contents)):
			f.write(str(j+1) + ". " + song_contents[j] + "\n")
print("Done.")