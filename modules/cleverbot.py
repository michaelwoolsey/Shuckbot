import cleverbot

with open("keys.txt", "r") as file:
    lines = file.read().splitlines()
    cbKey = lines[4]

cb = cleverbot.Cleverbot(cbKey)


def cleverbot_message(message, username):
    if len(message.clean_content) < len(username) + 2:
        return
    index = len(username) + 2
    return cb.say(message.clean_content[index:])
