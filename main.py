import reddit_tools
import os
import sys
import tools
import re
import time
import math
import traceback


def get_file_contents(file_name):
    result = []

    with open(file_name, 'r', encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith('#'):
                result.append(line)
    return result


def clean_up_text(text, word_regexes=None):
    # Strip accents
    text = tools.strip_accents(text)

    # Remove all non-alphanumeric characters (except - and ') by replacing with space
    text = re.sub(r'[^a-zA-Z0-9\-\'’]', ' ', text)
    # Replace ' with nothing
    text = re.sub(r'[\'’]', '', text)
    # Replace one or more dashes with a single space
    text = re.sub(r'-+', ' ', text)
    # Replace all whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading and trailing spaces
    text = text.strip()
    # Convert to lowercase
    text = text.lower()
    if word_regexes:
        # substitute whole words with their regex equivalent
        for word in word_regexes:
            text = re.sub(f"(\\W|^)({word})(?=\\W|$)", f"\\1{word_regexes[word]}", text,
                          flags=re.IGNORECASE | re.MULTILINE)
    # Replace a character repeated more than once with a single instance
    text = re.sub(r'([a-zA-Z\d])\1+', r'\1', text)

    return text


def get_original_lyrics(song):
    # Determine if the directory lyrics/original exists. Make it if not.
    if not os.path.exists('lyrics/original'):
        os.makedirs('lyrics/original')

    # Get the file name
    file_name = 'lyrics/original/' + song + '.txt'

    # If the file already exists, return the contents
    if os.path.exists(file_name):
        return get_file_contents(file_name)
    else:
        raise Exception(
            'No lyrics found for "' + song +
            '". Please add them through a text file in the lyrics/original directory. The file name should be the same as the song name.'
        )


def get_clean_lyrics(song, word_regexes):
    # Determine if the directory lyrics/clean exists. Make it if not.
    if not os.path.exists('lyrics/clean'):
        os.makedirs('lyrics/clean')

    # Get the file name
    file_name = 'lyrics/clean/' + song + '.txt'
    # Get the file name of the original lyrics
    original_file_name = 'lyrics/original/' + song + '.txt'

    # If the file already exists, return the contents
    if os.path.exists(file_name):
        return get_file_contents(file_name)
    elif os.path.exists(original_file_name):
        # get the file contents of the original lyrics and clean each line individually
        lyrics = get_original_lyrics(song)
        print("Ganerating clean lyrics for '" + song + "'")
        clean_lyrics = []
        for line in lyrics:
            line = line.strip()
            if not line.startswith('#'):
                clean_lyrics.append(clean_up_text(line, word_regexes))

        # Write the cleaned lyrics to the file
        with open(file_name, 'w', encoding="utf-8") as f:
            for line in clean_lyrics:
                f.write(line + '\n')
        return clean_lyrics
    else:
        raise Exception(
            'No lyrics found for "' + song +
            '". Please add them through a text file in the lyrics/original directory. The file name should be the same as the song name.'
        )


def get_word_regexes():
    result = {}

    file_name = "word_regexes.txt"
    if os.path.exists(file_name):
        lines = get_file_contents(file_name)
        for line in lines:
            parts = line.split('=')
            if len(parts) == 2:
                result[parts[0].strip()] = '='.join(parts[1:]).strip()
    else:
        # write an empty file
        with open(file_name, 'w', encoding="utf-8"):
            pass

    return result


def get_compatibility_mode(comment):
    compatibility_mode = re.search(r'Compatibility mode: (\d+)', comment.body)
    if compatibility_mode is None:
        return 1
    else:
        return int(compatibility_mode.group(1))


def get_user_blacklist():
    user_blacklist = []
    if os.path.exists('user_blacklist.txt'):
        user_blacklist = get_file_contents('user_blacklist.txt')
    else:
        # Write an empty blacklist to the file
        with open('user_blacklist.txt', 'w', encoding="utf-8"):
            pass
    return user_blacklist


def get_submission_ignore_list():
    submission_ignore_list = []
    if os.path.exists('submission_ignore_list.txt'):
        submission_ignore_list = get_file_contents('submission_ignore_list.txt')
    else:
        # Write an empty blacklist to the file
        with open('submission_ignore_list.txt', 'w', encoding="utf-8") as f:
            pass
    return submission_ignore_list


def update_user_blacklist(user_blacklist):
    # overwrite the user blacklist with the new one
    with open('user_blacklist.txt', 'w', encoding="utf-8"):
        for user in user_blacklist:
            f.write(user + '\n')


def update_submission_ignore_list(submission_ignore_list):
    # overwrite the submission ignore list with the new one
    with open('submission_ignore_list.txt', 'w', encoding="utf-8") as f:
        for submission in submission_ignore_list:
            f.write(submission + '\n')


def strip_lines(string):
    # Strip leading and trailing whitespace
    string = string.strip()
    lines = string.split('\n')
    # Strip leading and trailing whitespace from each line
    for i in range(len(lines)):
        lines[i] = lines[i].strip()
    return "\n".join(lines)


def get_songs():
    # Determine if the file "songs.txt" exists. Make it if not.
    if not os.path.exists('songs.txt'):
        with open('songs.txt', 'w', encoding="utf-8") as f:
            pass

    result = {}
    result["list"] = []
    result["urls"] = {}
    result["dict"] = {}

    for line in get_file_contents('songs.txt'):
        if line != "" and not line.startswith('#'):
            words = line.split(' ')
            result["list"].append(words[0])
            result["urls"][words[0]] = words[1]
            result["dict"][words[0]] = strip_lines(" ".join(words[2:]))

    return result


def count_matching_letters(word1, word2):
    # Count the number of matching letters between two words
    count = 0
    long_word = ""
    short_word = ""
    if len(word1) > len(word2):
        long_word = word1
        short_word = word2
    else:
        long_word = word2
        short_word = word1
    for i in range(len(short_word)):
        if short_word[i] == long_word[i]:
            count += 1
    return count


def close_match_count(lyrics, index, text):
    text = clean_up_text(text)
    result = 0
    match = re.search(lyrics[index] + "$", text)
    while index >= 0 and len(text) > 0 and match is not None:
        # removed the matched area from the text
        text = (text[:match.start()] + text[match.end():]).strip()
        result += 1
        index -= 1
        match = re.search(lyrics[index] + "$", text)

    return result


def close_match(song, index, text):
    text = clean_up_text(text)
    match_count = close_match_count(song, index, text)
    if match_count > 0:
        # join the matched lyrics together with a space
        joined = " ".join(song[index - match_count + 1:index + 1])
        # determine if the entire string matches this joined string
        return re.match("^" + joined + "$", text) is not None
    else:
        return False


def get_potential_lyric_indexes(song_dict, lyric):
    result = []
    clean_lyric = clean_up_text(lyric)
    for song_name in song_dict:
        if type(song_dict) is list:
            print(song_dict)
        song = song_dict[song_name]["clean_lyrics"]
        for i in range(len(song)):
            if close_match(song, i, clean_lyric):
                result.append({
                    "index": i,
                    "song": song_name,
                    "dict": song_dict[song_name]
                })
    return result


def get_lyric_extent(song, song_name, comment, index, username):
    current_comment = comment
    current_index = index
    current_extent = 0
    while current_index >= 0:
        if current_comment.author.name == username:
            # find the current position using regex "Current position: <current_position>"
            current_position = re.search(r'Current position: (\d+)', current_comment.body)
            if current_position is None:
                print(
                    "Found one of this bot's comments, but it doesn't have a current position. This marks the end of the previous chain.")
                return current_extent - 1
            else:
                current_position = int(current_position.group(1))
                if get_compatibility_mode(current_comment) > 1:
                    current_position -= 1

                if current_position == current_index:
                    # find the internal song name using regex "Internal song name: <internal_song_name>"
                    internal_song_name = re.search(r'Internal song name: (\w+)', current_comment.body)
                    if internal_song_name is None:
                        print(
                            "Found one of this bot's comments, but it doesn't have an internal song name. This marks the end of the previous chain.")
                        return current_extent
                    elif internal_song_name.group(1) == song_name:
                        # As we have guaranteed that this comment is the one that matches the chain, we return infinity so that it will be recognized as the highest extent
                        return math.inf
                    else:
                        print(
                            "Found one of this bot's comments, but it doesn't have the same internal song name as was specified. This marks the end of the previous chain.")
                        return current_extent
                else:
                    print(
                        "Found one of this bot's comments, but the position was not the same as was expected. This marks the end of the previous chain.")
                    return current_extent

        count = close_match_count(song, current_index, current_comment.body)
        if close_match(song, current_index, current_comment.body):
            current_extent += count
        else:
            return current_extent

        if reddit_tools.is_root_comment(current_comment):
            break

        current_comment = current_comment.parent()
        current_index -= count

    return current_extent


def get_lyric_index(song_dict, comment, username, potential_indexes=None):
    if not potential_indexes:
        potential_indexes = get_potential_lyric_indexes(song_dict, comment.body)

    if len(potential_indexes) == 0:
        return None
    elif len(potential_indexes) == 1:
        return potential_indexes[0]
    else:
        extent_array = []
        max_extent = 0
        max_extent_song = None
        for pair in potential_indexes:
            index = pair["index"]
            song_name = pair["song"]
            song = pair["dict"]["clean_lyrics"]

            extent = get_lyric_extent(song, song_name, comment, index, username)
            if extent is not None:
                extent_array.append({"extent": extent, "index": index, "song": song_name})
                if extent > max_extent:
                    max_extent = extent
                    max_extent_song = song_name

        # sort extent_array by index lowest to highest
        extent_array.sort(key=lambda x: x["index"])

        # return the index and song of the first element with the maximum extent
        for i in range(len(extent_array)):
            if extent_array[i]["extent"] == max_extent and extent_array[i]["song"] == max_extent_song:
                return {
                    "index": extent_array[i]["index"],
                    "song": max_extent_song
                }


def is_bottom_chain(song_dict, song_name, comment, username=reddit_tools.username):
    comment.refresh()
    if comment.replies is None:
        return True
    else:
        for reply in comment.replies:
            if reply.author.name == username:
                return False
            potential_indexes = get_potential_lyric_indexes(song_dict, clean_up_text(reply.body))
            for i in potential_indexes:
                if i["song"] == song_name:
                    return False
        return True


default_reply = strip_lines(
    """
		<next_line>

		---

		**I am a bot.** I have responded to this comment chain with the next lyric to the Encanto song "<friendly_song_name>"
		according to my best estimate of the current position.

		Am I Wrong? Suggest a correction [here](<song_url>).

		For more information (including how to report a bug), click [here](<help_link>).

		[Click to opt out](<optout_message_link>)

		[Click to opt in if currently opted out](<optin_message_link>)

		---

		Current position: <current_position>

		Internal song name: <internal_song_name>

		Compatibility mode: <compatibility_mode>
	"""
)

end_reply = strip_lines(
    """
		That's all the lyrics I have for the song "<friendly_song_name>".

		---

		**I am a bot.** This comment chain was for the Encanto song "<friendly_song_name>".

		Am I Wrong? Suggest a correction [here](<song_url>).

		For more information (including how to report a bug), click [here](<help_link>).

		[Click to opt out](<optout_message_link>)

		[Click to opt in if currently opted out](<optin_message_link>)

		---

		Current position: <current_position>

		Internal song name: <internal_song_name>

		Compatibility mode: <compatibility_mode>
	"""
)

ignore_post_reply = strip_lines(
    """
		I will no longer respond to any comments in this post. To reverse, contact the owner (u/00PT)
		with a link to the post.

		Have a nice day!
	"""
)
help_link = "https://www.reddit.com/r/Encanto_LyricBot/comments/tesdvp/encanto_lyric_bot_faq/"


def format_reply(next_line, current_position, internal_song_name, friendly_song_name, help_link, owner, username,
                 compatibility_mode, song_url, optout_message_link, optin_message_link, reply_base=default_reply):
    if compatibility_mode > 1:
        current_position += 1

    reply = reply_base.replace('<next_line>', next_line)
    reply = reply.replace('<current_position>', str(current_position))
    reply = reply.replace('<internal_song_name>', internal_song_name)
    reply = reply.replace('<friendly_song_name>', friendly_song_name)
    reply = reply.replace('<help_link>', help_link)
    reply = reply.replace('<owner>', owner)
    reply = reply.replace('<username>', username)
    reply = reply.replace('<compatibility_mode>', str(compatibility_mode))
    reply = reply.replace('<song_url>', song_url)
    reply = reply.replace('<optout_message_link>', optout_message_link)
    reply = reply.replace('<optin_message_link>', optin_message_link)
    return reply


def main(args=None):
    songs = get_songs()
    song_list = songs["list"]
    song_friendly_names = songs["dict"]
    song_urls = songs["urls"]

    if not args:
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
                },

                {
                    'name': 'compatibility mode',
                    'target_type': int,
                    'input_args': {
                        'invalid_message': 'Compatibility mode must be an integer.',
                        'cancel': 'default'
                    },
                    'default': 1,
                }
            ], False)

    # get the start time from "start_time.txt"
    process_start_time = float(get_file_contents("start_time.txt")[0])

    subreddit = reddit_tools.reddit.subreddit(args['subreddit']) if args[
                                                                        'subreddit'] != 'default' else reddit_tools.test_subreddit
    comment_limit = args['comment limit'] if args['comment limit'] != 'default' else 1000
    max_age_hours = args['max age (hours)'] if args['max age (hours)'] != 'default' else 24.0
    compatibility_mode = args['compatibility mode'] if args['compatibility mode'] != 'default' else 1

    print("Specified subreddit: " + args['subreddit'])
    print("Specified Comment limit: " + str(comment_limit))
    print("Specified Max age: " + str(max_age_hours))
    print("Specified Compatibility mode: " + str(compatibility_mode))

    print("Getting word regexes")
    word_regexes = get_word_regexes()

    song_dict = {}
    for song in song_list:
        print("Getting original lyrics for '" + song + "'")
        original_lyrics = get_original_lyrics(song)
        print("Getting clean lyrics for '" + song + "'")
        clean_lyrics = get_clean_lyrics(song, word_regexes)

        ignore_indexes = []
        for i in range(len(original_lyrics)):
            if original_lyrics[i][0] == "^":
                ignore_indexes.append(i)
                original_lyrics[i] = original_lyrics[i][1:].strip()

        continue_indexes = []
        for i in range(len(original_lyrics)):
            if original_lyrics[i].endswith("->"):
                continue_indexes.append(i)
                original_lyrics[i] = original_lyrics[i][:-2].strip()

        song_dict[song] = {
            "original_lyrics": original_lyrics,
            "clean_lyrics": clean_lyrics,
            "ignore_indexes": ignore_indexes,
            "continue_indexes": continue_indexes
        }

    """print("Getting subreddit moderators")
	mods = reddit_tools.get_mods(subreddit)"""

    print("Getting user blacklist")
    user_blacklist = get_user_blacklist()
    submission_ignore_list = get_submission_ignore_list()

    print("checking for user blacklist additions and submissions to ignore")
    opt_in_text = "!optin"
    opt_out_text = "!optout"
    ignore_submission_text = "!ignorepost"

    optout_message_link = f"https://www.reddit.com/message/compose?to=%2Fu%2F{reddit_tools.username}&subject={opt_out_text}&message=Send%20This%20Message%20To%20Opt%20Out"
    optin_message_link = f"https://www.reddit.com/message/compose?to=%2Fu%2F{reddit_tools.username}&subject={opt_in_text}&message=Send%20This%20Message%20To%20Opt%20In"

    # search for comments
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
                reddit_tools.reply_to_comment(comment,
                                              "You have opted back in to this bot's services. Have a nice day!")

            if body.lower() == ignore_submission_text.lower():
                comment.refresh()
                if comment.link_id in submission_ignore_list:
                    continue
                submission_id = comment.link_id
                submission_ignore_list.append(submission_id)
                print("Submission " + submission_id + " has been ignored.")
                reddit_tools.reply_to_comment(comment, ignore_post_reply)

    # search for messages
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
                reddit_tools.reply_to_message(message,
                                              "You have opted back in to this bot's services. Have a nice day!")

    update_user_blacklist(user_blacklist)
    update_submission_ignore_list(submission_ignore_list)

    requests_used = reddit_tools.reddit.auth.limits['used']

    # Get a list of comments in the subreddit. Time how long this takes.
    print("Getting comments")
    start_time = time.time()
    comments = reddit_tools.get_comments(subreddit, comment_limit)
    # sort comments by age (newest first)
    comments = sorted(comments, key=lambda x: x.created_utc, reverse=True)
    total_comments = len(comments)

    if total_comments == 0:
        print("No comments found.")
        sys.exit()

    handled_comments = 0
    replied_comments = 0
    print(f"Got {total_comments} comments in {str(time.time() - start_time)} seconds")

    # Loop through the comments. Time how long this takes.
    print("Handling comments")
    start_time = time.time()
    for comment in comments:
        if comment.author:
            age = (time.time() - comment.created_utc) / 3600
            # Don't handle the comment if it's too old
            if age > max_age_hours:
                print(f"Found comment '{comment.id}' that is too old ({age} hours). Stopping here...")
                # Stop processing additional comments, since all the rest are going to be too old
                break

            # Don't handle the comment if it was made after process_start_time
            if comment.created_utc > process_start_time:
                print(
                    f"Found comment '{comment.id}' that was made after process start time ({process_start_time}). Skipping...")
                continue

            """#Don't handle the comment if it is a root comment made by a moderator
			if comment.author.name in mods and reddit_tools.is_root_comment(comment):
				print(f"Found root comment '{comment.id}' made by a moderator. Skipping...")
				continue"""

            # Don't handle the comment if it is  made by a blacklisted user
            if comment.author.name in user_blacklist:
                print(f"Found comment '{comment.id}' made by a blacklisted user (u/{comment.author}). Skipping...")
                continue

            # Don't handle the comment if it's made by the bot
            if comment.author.name == reddit_tools.username:
                print(f"Found comment '{comment.id}' by this bot. Skipping...")
                continue

            # Don't handle the comment if we have already replied to a comment further down the chain
            if reddit_tools.did_reply_comment(comment, require_root=False):
                print(f"Found comment '{comment.id}' already replied to. Skipping...")
                continue

            # Don't handle the comment if it belongs to a submission that has been ignored
            if not hasattr(comment, "link_id"):
                # refresh the comment to populate the link_id property
                comment.refresh()
            if comment.link_id in submission_ignore_list:
                print(f"Found comment '{comment.id}' in an ignored submission. Skipping...")
                continue

            # print(f"Found comment '{comment.id}' by '{comment.author.name}'. Body:")
            formatted_body = clean_up_text(comment.body)
            # print(f"\t{formatted_body}")

            print("Found comment '" + comment.id + "' by '" + comment.author.name + "' that could be a match.")
            print("Formatted Text: " + formatted_body)
            potential_indexes = get_potential_lyric_indexes(song_dict, formatted_body)
            potential_indexes_str = []
            for index in potential_indexes:
                potential_indexes_str.append({})
                potential_indexes_str[-1]["index"] = index["index"]
                potential_indexes_str[-1]["song"] = index["song"]
            print("Potential indexes: " + str(potential_indexes_str))

            if len(potential_indexes) > 0:
                lyric_index = get_lyric_index(song_dict, comment, reddit_tools.username,
                                              potential_indexes=potential_indexes)
                if lyric_index == None:
                    print(f"No match found. Skipping...")
                    handled_comments += 1
                    continue

                current_position = lyric_index["index"]
                song_name = lyric_index["song"]
                song_url = song_urls[song_name]
                original_lyrics = song_dict[song_name]["original_lyrics"]
                clean_lyrics = song_dict[song_name]["clean_lyrics"]
                ignore_indexes = song_dict[song_name]["ignore_indexes"]
                continue_indexes = song_dict[song_name]["continue_indexes"]

                if is_bottom_chain(song_dict, song_name, comment):
                    # current_position += 1
                    print(f"Match Position: {current_position}")
                    print(f"Match Song: {song_name}")
                    extent = get_lyric_extent(clean_lyrics, song_name, comment, current_position, reddit_tools.username)

                    if current_position + 1 != len(clean_lyrics) or extent > 1:
                        if current_position in ignore_indexes and extent <= 1:
                            print("Found a match, but it's an ignored lyric and at the beginning of a chain.")
                            print("We don't start chains with ignored lyrics. Skipping...")
                            handled_comments += 1
                            continue

                        if current_position == len(clean_lyrics) - 1:
                            print(f"Found match at the end of the song.")
                            print("replying to indicate this...")
                            reply = format_reply(original_lyrics[current_position], current_position, song_name,
                                                 song_friendly_names[song_name], help_link, reddit_tools.owner,
                                                 reddit_tools.username, compatibility_mode, song_url,
                                                 optout_message_link, optin_message_link, reply_base=end_reply)
                            reddit_tools.reply_to_comment(comment, reply)
                            handled_comments += 1
                            continue

                        next_position = current_position + 1
                        next_line = original_lyrics[next_position]
                        while next_position in continue_indexes and next_position < len(clean_lyrics) - 1:
                            next_position += 1
                            print("Continuing to position " + str(next_position) + " as it's a continue index.")
                            next_line += " " + original_lyrics[next_position]

                        print("Extent: " + str(extent))
                        print("replying...")
                        reply = format_reply(next_line, next_position, song_name, song_friendly_names[song_name],
                                             help_link, reddit_tools.owner, reddit_tools.username, compatibility_mode,
                                             song_url, optout_message_link, optin_message_link)
                        my_reply = reddit_tools.reply_to_comment(comment, reply)
                        if (next_position) == len(clean_lyrics) - 1:
                            print(f"Just replied with the last line of the song.")
                            print("replying to indicate this...")
                            reply = format_reply(original_lyrics[current_position + 1], current_position + 1, song_name,
                                                 song_friendly_names[song_name], help_link, reddit_tools.owner,
                                                 reddit_tools.username, compatibility_mode, song_url,
                                                 optout_message_link, optin_message_link, reply_base=end_reply)
                            reddit_tools.reply_to_comment(my_reply, reply)
                        replied_comments += 1
                    else:
                        print(
                            "Not replying because the next line is the last line of the song and there is no evidence of a preexisting chain.")

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
    # split into minutes and seconds
    minutes = int(math.floor(seconds_until_reset / 60))
    seconds = str(int(round(seconds_until_reset % 60)))
    if len(seconds) == 1:
        seconds = "0" + seconds
    print(f"Approximate time until reset (upper bound): {minutes}:{seconds}")

    ignored_comments = total_comments - handled_comments
    print(
        f"Handled {handled_comments} out of {total_comments} ({ignored_comments} ignored; {replied_comments} replied to; {(handled_comments / total_comments) * 100}% coverage) comments in {str(time.time() - start_time)} seconds")
    print(f"Used a total of {limit_info['used'] - requests_used} requests in this instance of the script.")


if __name__ == "__main__":
    print("It is recommended that you run 'launcher.py' to launch the bot instead of running this script directly.")

    # store the current time inside "start_time.txt" Overwrite if it exists. Create if it doesn't.
    with open('start_time.txt', 'w', encoding="utf-8") as f:
        f.write(str(time.time()))

    try:
        print("Starting...")
        print("")
        main()
        print("")
        print("Successfully ran the bot.")
    except Exception as e:
        print("")
        print("Error running bot")
        print(traceback.format_exc())

    # delete the start_time.txt file
    os.remove('start_time.txt')
