import cleverbot

params = {}

with open("keys.txt", "r") as file:
    lines = file.read().splitlines()
    for line in lines:
        x = line.split("=")
        if len(x) == 2:
            params[x[0]] = x[1]

cb = cleverbot.Cleverbot(params["token"])

def cleverbot_message(message, username):
    if len(message.clean_content) < len(username) + 2:
        return
    index = len(username) + 2
    return cb.say(message.clean_content[index:])
