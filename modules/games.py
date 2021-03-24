import discord
from PIL import Image, ImageChops, ImageColor
import numpy as np
import random
import time
from colormath.color_objects import XYZColor, sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cmc
import asyncio
import requests
from io import BytesIO
import json
from typing import List, Tuple, Optional

async def game(message, client):
    try:
        args = [x.lower() for x in message.clean_content[1:].split(' ')][1:]
    except IndexError:
        await message.channel.send("**The list of available games are:**\n\t*;game colour* - guess the hexcode!")
        return
    if args[0] in ("color", "col", "c"):
        if len(args) > 2 and args[1] in ("m", "mp", "multi", "multiplayer") and args[2].isdigit():
            await colour_guesser_multi(message, client, game_time=int(args[2]))
        elif len(args) > 1 and args[1] in ("m", "mp", "multi", "multiplayer"):
            await colour_guesser_multi(message, client)
        else:
            await colour_guesser(message, client)
    elif args[0] == "colour":
        if len(args) > 1 and args[1] in ("m", "mp", "multi", "multiplayer"):
            await colour_guesser_multi(message, client, "u")
        else:
            await colour_guesser(message, client, "u")
    elif args[0] in ("flag", "flags", "f"):
        if len(args) == 1:
            await flag_guesser(message, client)
        elif args[1] in ("easy", "e", "1"):
            await flag_guesser(message, client, 1)
        elif args[1] in ("normal", "n", "2"):
            await flag_guesser(message, client, 2)
        elif args[1] in ("hard", "h", "3"):
            await flag_guesser(message, client, 3)
        elif args[1] in ("states", "s", "4"):
            await flag_guesser(message, client, 4)
        elif args[1] in ("expert", "extreme", "x", "5"):
            await flag_guesser(message, client, 5)
        elif args[1] in ("master", "all", "m", "a", "6"):
            await flag_guesser(message, client, 6)
        elif args[1] in ("japan", "j", "7"):
            await flag_guesser(message, client, 7)
        else:
            await flag_guesser(message, client)
    elif args[0] in ["geography", "geo", "g"]:
        area = geo_get_area(args)
        mode = geo_get_mode(args)
        await geography_game(message, client, area, mode)


def geo_get_area(args) -> str:
    if list_contains(args, ['japan', 'j', 'prefectures', 'p', 'pf']):
        return 'japan'
    return ""


def geo_get_mode(args) -> str:
    if list_contains(args, ['map', 'm']):
        return 'map'
    return ""


def list_contains(l1, l2) -> bool:
    for i in l1:
        if i.lower() in l2:
            return True
    return False


async def colour_guesser(message, client, _letter=""):
    size = 150
    mention = message.author.mention
    col = hex(random.getrandbits(24))[2:]
    while len(col) < 6:
        col = '0' + col
        print(col)

    try:
        img = Image.new("RGB", (size, size), ImageColor.getcolor(('#' + col), "RGB"))
    except ValueError:
        await message.channel.send("Value Error has been thrown!")
        return
    else:
        img.save("colourguess.png")
        await message.channel.send(mention + ", here is your colo" + _letter + "r! Try to guess its hex code!",
                                   file=discord.File("colourguess.png"))

    def check(m):
        return m.author == message.author and m.channel == message.channel

    t = time.time()
    msg = await client.wait_for('message', check=check)
    new_time = time.time()
    msg_content = msg.content

    if msg_content[0] == '#':
        msg_content = msg_content[1:]

    def is_hex(s):
        try:
            int(s, 16)
            return True
        except ValueError:
            return False

    if len(msg_content) != 6 or not is_hex(msg_content):
        await message.channel.send(
            "Sorry, your answer was not formatted correctly! Your answer should just be the 6 digit "
            "hexadecimal code for your guess, and nothing else! The actual colo" + _letter + "r was "
            + col + " !")
        return

    r = int(msg_content[0:2], 16)
    g = int(msg_content[2:4], 16)
    b = int(msg_content[4:6], 16)

    ar = int(col[0:2], 16)
    ag = int(col[2:4], 16)
    ab = int(col[4:6], 16)

    score = calculate_score(r, g, b, ar, ag, ab)
    letter = "s"
    if score == 1:
        letter = ''

    img.paste(Image.new("RGB", (size // 2, size), ImageColor.getcolor(('#' + msg_content), "RGB")),
              (size // 2, 0))
    img.save("clrguessresult.png")

    await message.channel.send("The actual colo" + _letter + "r was " + col + "!\n" + mention + " got " +
                               str(int(score)) + "/100 point" + letter + "\n"
                                                                         "You took %.1f seconds to guess!"
                               % (new_time - t), file=discord.File("clrguessresult.png"))


async def colour_guesser_multi(message, client, _letter="", game_time=15):
    if game_time > 60:
        game_time = 60
    size = 150
    col = hex(random.getrandbits(24))[2:]
    while len(col) < 6:
        col = '0' + col
        print(col)
    try:
        img = Image.new("RGB", (size, size), ImageColor.getcolor(('#' + col), "RGB"))
    except ValueError:
        await message.channel.send("Value Error has been thrown!")
        return
    else:
        img.save("colourguess.png")
        msg = await message.channel.send("Here is your colo" + _letter + "r! Everyone try to guess its hex code!"
                                                                         "\nYou have " + str(game_time) + " seconds...",
                                         file=discord.File("colourguess.png"))

    def is_valid_hex(s):
        try:
            int(s, 16)
            return len(s) == 6
        except ValueError:
            return False

    await asyncio.sleep(game_time)
    msgs = message.channel.history(limit=50)
    guess_msgs = []
    users = []
    final_guesses = []
    winner = [0, "", -1]
    async for x in msgs:
        if x.id == msg.id:
            break
        if is_valid_hex(x.clean_content):
            guess_msgs.append(x)

    for x in guess_msgs:
        if x.author.id in users:
            continue
        final_guesses.append([x.author.id, x.clean_content])
        users.append(x.author.id)

    ar = int(col[0:2], 16)
    ag = int(col[2:4], 16)
    ab = int(col[4:6], 16)

    for x in range(0, len(final_guesses)):
        rs = final_guesses[x][1][0:2]
        gs = final_guesses[x][1][2:4]
        bs = final_guesses[x][1][4:6]
        r = int(rs, 16)
        g = int(gs, 16)
        b = int(bs, 16)
        score = calculate_score(r, g, b, ar, ag, ab)
        final_guesses[x] = [final_guesses[x][0], final_guesses[x][1], score]
        if score > winner[2]:
            winner = final_guesses[x]

    if not final_guesses:
        await message.channel.send("Time out! Nobody guessed!")
    else:
        final_guesses.sort(key=lambda y: y[2], reverse=True)
        guesses = len(final_guesses)
        for x in range(0, guesses):
            img.paste(Image.new("RGB", (size // 2, size), ImageColor.getcolor(('#' + final_guesses[x][1]), "RGB")),
                      (size // 2, x * size // guesses))
        img.save("clrguessresult.png")
        await message.channel.send(
            "The actual colo" + _letter + "r was " + col + "!\n" + client.get_user(int(winner[0])).mention
            + " got " + str(int(np.ceil(winner[2]))) + "/100 points\n", file=discord.File("clrguessresult.png"))
        to_send = ""
        for x in range(0, len(final_guesses)):
            to_send += str(x + 1) + ". " + client.get_user(final_guesses[x][0]).mention + ": " + \
                       str(int(np.ceil(final_guesses[x][2]))) + "/100 points (#" + final_guesses[x][1] + ")\n"
        await message.channel.send(to_send)


def rgb_to_lab(r, g, b):
    cr = r / 255
    cg = g / 255
    cb = b / 255

    rgb_obj = sRGBColor(cr, cg, cb)
    xyz_obj = convert_color(rgb_obj, XYZColor)
    return convert_color(xyz_obj, LabColor)


def calculate_score(r, g, b, ar, ag, ab):
    lab_obj = rgb_to_lab(r, g, b)
    a_lab_obj = rgb_to_lab(ar, ag, ab)

    difference = delta_e_cmc(lab_obj, a_lab_obj)
    res = (100 - (difference - 2) ** 0.7 * (23 / 3)) if difference > 2 else 100
    return res if res > 0 else 0


async def flag_guesser(message, client, difficulty=0):
    lengths = [0 for _ in range(8)]
    type_f = ["country", "country", "country", "country", "state", "flag", "flag", "Japanese Prefecture", "flag", "flag", "flag", "flag"]
    with open('modules/flags.json') as f:
        flags = json.load(f)
    # print(flags[1])
    for c in flags:
        lengths[c["difficulty"]-1] += 1
    # print(lengths)
    min_index = 0
    game_time = 15

    if difficulty == 1:
        max_index = lengths[0]
    elif difficulty == 2:
        min_index = lengths[0] + 1
        max_index = lengths[0] + lengths[1]
    elif difficulty == 3:
        min_index = lengths[0] + lengths[1] + 1
        max_index = lengths[0] + lengths[1] + lengths[2]
    elif difficulty == 4:
        min_index = lengths[0] + lengths[1] + lengths[2] + 1
        max_index = lengths[0] + lengths[1] + lengths[2] + lengths[3]
    elif difficulty == 5:
        min_index = lengths[0] + lengths[1] + lengths[2] + 1
        max_index = lengths[0] + lengths[1] + lengths[2] + lengths[3] + lengths[4]
    elif difficulty == 6:
        max_index = len(flags)
    elif difficulty == 7:
        min_index = lengths[0] + lengths[1] + lengths[2] + lengths[3] + lengths[4] + 1
        max_index = len(flags)  # WILL HAVE TO CHANGE  lengths[0] + lengths[1] + lengths[2] + lengths[3] + lengths[4] + lengths[6]
    else:
        max_index = lengths[0] + lengths[1] + lengths[2]

    try:
        country_index = random.randint(min_index, max_index)
    except ValueError:
        print(f"uh oh! value error raised: {min_index, max_index, len(flags), lengths}")
        country_index = random.randint(0, len(flags))

    current_flag = flags[country_index]
    response = requests.get(current_flag["url"])
    flag_img = Image.open(BytesIO(response.content))
    flag_img.save("flag.png")

    embed = discord.Embed(title="You have " + str(game_time) + " seconds to guess the " + type_f[difficulty] + "!")
    embed.colour = discord.Color.gold()
    embed.type = "rich"

    embed.set_image(url="attachment://flag.png")
    await message.channel.send(embed=embed, file=discord.File("flag.png"))
    # await message.channel.send("You have " + str(game_time) + " seconds to guess the flag!", file=discord.File("flag.png"))

    def check(m):
        if type(current_flag["name"]) is list:
            for n in current_flag["name"]:
                if n.lower() == m.content.lower() and m.channel == message.channel:
                    return True
            return False
        return m.channel == message.channel and (m.content.lower() == current_flag["name"].lower())

    temp = 0

    try:
        msg = await client.wait_for('message', check=check, timeout=game_time)
    except asyncio.TimeoutError:
        try:
            await message.channel.send("Sorry, nobody got the " + type_f[difficulty] + " correct! The correct answer was: " + current_flag["name"])
        except TypeError:
            await message.channel.send("Sorry, nobody got the " + type_f[difficulty] + " correct! The correct answer was: " + current_flag["name"][0])
        return
    try:
        temp = 1
        await message.channel.send("Good job " + msg.author.mention + "! The " + type_f[difficulty] + " was " + current_flag['name'])
    except TypeError:
        temp = 2
        await message.channel.send("Good job " + msg.author.mention + "! The " + type_f[difficulty] + " was " + current_flag['name'][0])

    if temp != 0:

        increment_user(msg.author.mention, "flag", difficulty_=difficulty, flag=current_flag["name"], total=1)

async def geography_game(message, client, area="japan", mode="map", game_time=15):
    if area == "":
        print("empty area")
        area = "japan"

    if mode == "":
        print('empty mode')
        mode = "map"

    if area == "japan":
        with open('modules/prefectures.json') as f:
            geo = json.load(f)

    if mode == "map":
        await geography_map(message, client, area, mode, geo, game_time)


async def geography_map(message, client, area, mode, geo, game_time):
    index = random.randint(0, len(geo) - 1)
    pref = geo[index]
    try:
        response = requests.get(pref["map_url"])
    except:
        print(geo[index])
        await message.channel.send(f"Something broke! Please try the command again")
        return

    map_img = Image.open(BytesIO(response.content))
    map_img.save("map.png")

    embed = discord.Embed(title=f"You have {str(game_time)} seconds to guess the prefecture based on the map!")
    embed.colour = discord.Color.gold()
    embed.type = "rich"

    embed.set_image(url="attachment://map.png")
    await message.channel.send(embed=embed, file=discord.File("map.png"))

    def check(m):
        return m.channel == message.channel and (m.content.lower() == pref["name"][0].lower())

    try:
        msg = await client.wait_for('message', check=check, timeout=game_time)
        await message.channel.send(f"Good job {msg.author.mention}! The prefecture was {pref['name'][0]}")
        increment_user(msg.author.mention, 'geography', area=area, mode=mode)

    except asyncio.TimeoutError:
        await message.channel.send(f"Sorry, nobody got the prefecture correct! The correct answer was: {pref['name'][0]}")


def increment_user(user_mention, game_played: str, **kwargs):
    # kwargs will contain any information important to the game
    # game_played MUST be one of 'color', 'flag', or 'geography'
    GAMES = ['color', 'flag', 'geography']
    if game_played not in GAMES:
        print('u messed up mikey')
        return

    kwargs_combo_string = ""
    for key, value in kwargs.items():
        kwargs_combo_string += str(value) + '_'

    with open('modules/scores.json') as f:
        df = json.load(f)

    if user_mention not in df:  # user does not exist in the file
        df[user_mention] = {}
        for game__ in GAMES:
            df[user_mention][game__] = {}

    if df[user_mention][game_played] == {}:  # uninitialized
        for key, value in kwargs.items():
            # print(key, value)
            if key[-1] == '_':
                df[user_mention][game_played][key+str(value)] = 1
            elif type(value) == str:
                df[user_mention][game_played][key] = {value: 1, kwargs_combo_string: 1}
            elif isinstance(value, list):
                df[user_mention][game_played][key] = {value[0]: 1}
            else:
                df[user_mention][game_played][key] = value

    else:  # game played before
        # print(1)
        for key, value in kwargs.items():
            if key[-1] == '_':
                try:
                    df[user_mention][game_played][key + str(value)] += 1
                except KeyError:
                    df[user_mention][game_played][key + str(value)] = 1
            elif type(value) == str:
                # print(key, value)
                # print(f'{df[user_mention]},\n{df[user_mention][game_played]}, \n{df[user_mention][game_played][key]}')
                df[user_mention][game_played][key][value] += 1
                df[user_mention][game_played][key][kwargs_combo_string] += 1
            elif isinstance(value, list):
                # print(df[user_mention][game_played], key, value)
                if value[0] in df[user_mention][game_played][key]:
                    df[user_mention][game_played][key][value[0]] += 1
                else:
                    df[user_mention][game_played][key][value[0]] = 1
            elif type(value) == int:
                df[user_mention][game_played][key] += value
            else:
                df[user_mention][game_played][key] = value
                print("! not int or strng")

    with open('modules/scores.json', 'w') as f:  # likely to cause issues! race condition
        json.dump(df, f, indent=4)

