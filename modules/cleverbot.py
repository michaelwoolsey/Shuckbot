import cleverbot
from modules import parameters

cb = cleverbot.Cleverbot(parameters.params["cleverbot"])


def cleverbot_message(message, username):
    if len(message.clean_content) < len(username) + 2:
        return
    index = len(username) + 2
    return cb.say(message.clean_content[index:])
