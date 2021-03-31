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
from typing import Optional, List, Any


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
        elif list_contains(['m', 'multi', 'multiplayer'], args):
            diffs_ = []
            for arg in args[1:]:
                diffs_.append(get_diff_from_arg(arg))
            diff = max(0, *diffs_)  # if no difficulty inputted, just do diff=0
            points_to_win = get_int_from_args(args)
            # print(f'diff:{diff}, ptw:{points_to_win}')
            if points_to_win != -1:  # did input round count
                await flag_guesser_multi(message, client, difficulty=diff, points_to_win=points_to_win)
            else:
                await flag_guesser_multi(message, client, difficulty=diff)
        else:
            await flag_guesser(message, client, get_diff_from_arg(args[1]))
    elif args[0] in ["geography", "geo", "g"]:
        area = geo_get_area(args)
        mode = geo_get_mode(args)
        await geography_game(message, client, area, mode)
    elif args[0] in ["stats", "s"]:
        if message.mentions: #has mentions
            user_mention = message.mentions[0].mention
        else:
            user_mention = message.author.mention
        if list_contains(['color', 'colour', 'col', 'c'], args[1:]):
            user_game = 'color'
        elif list_contains(['flag', 'flags', 'f'], args[1:]):
            user_game = 'flag'
        elif list_contains(['geography', 'geo', 'g'], args[1:]):
            user_game = 'geography'
        else:
            user_game = 'all'
        await get_stats(message, client, user_mention, user_game)
    elif args[0] in ['leaderboard', 'leader', 'top', 'l']:
        await get_leaderboard(message, client)


def get_diff_from_arg(arg: str) -> int:
    # returns the difficulty for the flag game
    if arg in ("easy", "e"):
        return 1
    elif arg in ("normal", "n"):
        return 2
    elif arg in ("hard", "h"):
        return 3
    elif arg in ("states", "s"):
        return 4
    elif arg in ("expert", "extreme", "x"):
        return 5
    elif arg in ("all", "a"):
        return 6
    elif arg in ("japan", "j"):
        return 7
    return 0


def get_int_from_args(args) -> int:
    # returns -1 if no ints found
    for arg in args:
        if arg.isdigit():
            return int(arg)
    return -1


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


def list_contains_return(l1, l2) -> Optional[Any]:
    for i in l1:
        if i.lower() in l2:
            return i


async def username_from_mention(mention, client) -> str:
    name = str(mention)[2:-1].replace("!", "")
    name = await client.fetch_user(int(name))
    return str(name)


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


def get_flag(message, difficulty):
    lengths = [0 for _ in range(8)]
    with open('modules/flags.json') as f:
        flags = json.load(f)
    # print(flags[1])
    for c in flags:
        lengths[c["difficulty"] - 1] += 1
    # print(lengths)
    min_index = 0

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
        max_index = len(
            flags)  # WILL HAVE TO CHANGE  lengths[0] + lengths[1] + lengths[2] + lengths[3] + lengths[4] + lengths[6]
    else:
        max_index = lengths[0] + lengths[1] + lengths[2]

    try:
        country_index = random.randint(min_index, max_index - 1)
    except ValueError:
        print(f"uh oh! value error raised: {min_index, max_index - 1, len(flags), lengths}")
        country_index = random.randint(0, len(flags))

    try:
        current_flag = flags[country_index]
        response = requests.get(current_flag["url"])
        flag_img = Image.open(BytesIO(response.content))
        flag_img.save("flag.png")
    except:
        print(country_index)
        return

    return current_flag


async def flag_guesser(message, client, difficulty=0, game_time=15):
    type_f = ["country", "country", "country", "country", "state", "flag", "flag", "Japanese Prefecture", "flag", "flag", "flag", "flag"]

    current_flag = get_flag(message, difficulty)
    if current_flag is None:
        await message.channel.send('Sorry, something went wrong! Please try again')
        return

    # print(current_flag)

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


async def flag_guesser_multi(message, client, difficulty=0, points_to_win=5, game_time=15):
    points_to_win = max(min(points_to_win, 30), 2)
    msg1 = await message.channel.send(f'Get ready to guess the flag! The first person to correctly guess {points_to_win} flags wins!')
    type_f = ["country", "country", "country", "country", "state", "flag", "flag", "Japanese Prefecture", "flag",
              "flag", "flag", "flag"]

    current_flag = None
    sent_embed = None
    user_points = {}
    losses_in_a_row = 0

    def check(m):
        if type(current_flag["name"]) is list:
            for n in current_flag["name"]:
                if n.lower() == m.content.lower() and m.channel == message.channel:
                    return True
            return False
        return m.channel == message.channel and (m.content.lower() == current_flag["name"].lower())

    rounds_played = 1
    while True:
        current_flag = get_flag(message, difficulty)
        if current_flag is None:
            await message.channel.send('Sorry, something went wrong! Please try again')
            return

        if sent_embed is not None:
            sent_embed.delete()

        # await message.channel.send(f'Sorry, something went wrong! Please try again')

        embed = discord.Embed(title=f"You have {game_time} seconds to guess the {type_f[difficulty]}!")
        embed.set_footer(text=f"Round {rounds_played}, First to {points_to_win} wins!")
        embed.colour = discord.Color.gold()
        embed.type = "rich"
        embed.set_image(url="attachment://flag.png")
        sent_embed = await message.channel.send(embed=embed, file=discord.File("flag.png"))

        temp = 0

        try:
            msg = await client.wait_for('message', check=check, timeout=game_time)
            temp = 1
            losses_in_a_row = 0
            await message.channel.send(
                f"Good job {msg.author.mention}! The {type_f[difficulty]} was {current_flag['name'][0]}")

        except asyncio.TimeoutError:
            await message.channel.send(
                f"Sorry, nobody got the {type_f[difficulty]} correct! The correct answer was: {current_flag['name'][0]}")
            losses_in_a_row += 1
            if losses_in_a_row == 3:
                await message.channel.send("If nobody gets this next one correct, the game will end!")
            if losses_in_a_row > 3:
                await message.channel.send("Game over! Nobody wins :(")
                return

        if temp != 0:  # somebody won
            increment_user(msg.author.mention, "flag", difficulty_=difficulty, flag=current_flag["name"], total=1, rounds_won=1)
            if msg.author.mention not in user_points:
                user_points[msg.author.mention] = 1
            else:
                user_points[msg.author.mention] += 1
                if user_points[msg.author.mention] >= points_to_win:
                    await message.channel.send(f'Congratulations {msg.author.mention}! You are our winner!')
                    increment_user(msg.author.mention, "flag", games_won=1)
                    temp = -1

        embed2 = discord.Embed(title=f"Scoreboard!")
        for player, points in sorted(user_points.items(), key=lambda item: item[1], reverse=True):
            name = await username_from_mention(player, client)
            embed2.add_field(name=name, value=points, inline=False)
        embed2.colour = discord.Color.blurple()
        embed2.type = "rich"
        sent_embed2 = await message.channel.send(embed=embed2)
        if temp == -1:  # game over
            return

        rounds_played += 1


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


async def get_stats(message, client, user_mention, user_game):
    with open('modules/scores.json') as f:
        db = json.load(f)

    user_name = await username_from_mention(user_mention, client)
    user_mention = str(user_mention).replace("!", "")

    if user_game == 'color':
        await message.channel.send(f"Sorry! There are no stats for that game yet!")
    elif user_game == 'flag':
        try:
            total = db[user_mention]['flag']['total']
        except:
            await message.channel.send(f"{user_name[:-5]} has not played this game yet!")
            return

        embed = discord.Embed(title=f"Stats for user {user_name[:-5]} for the Flag game")
        embed.set_footer(text=f"Stat collection started 3/23/2021")
        embed.colour = discord.Colour.red()
        embed.type = "rich"

        embed.add_field(name=f'Flags correctly guessed:', value=f'{total}')

        try:
            embed.add_field(name=f"Rounds won in multiplayer:", value=f"{db[user_mention]['flag']['rounds_won']}")
        except:
            embed.add_field(name=f"Rounds won in multiplayer:", value=f"0")
        try:
            embed.add_field(name=f"Games won in multiplayer:", value=f"{db[user_mention]['flag']['games_won']}")
        except:
            embed.add_field(name=f"Games won in multiplayer:", value=f"0")

        sent_embed = await message.channel.send(embed=embed)

    elif user_game == 'geography':
        pass
    else:  # general
        try:
            total = db[user_mention]['flag']['total']
        except:
            await message.channel.send(f"{user_name[:-5]} has not played this game yet!")
            return

        embed = discord.Embed(title=f"Stats for user {user_name[:-5]}")
        embed.set_footer(text=f"Stat collection started 3/23/2021\nFor more stats, add the name of the game to your mesage!")
        embed.colour = discord.Colour.red()
        embed.type = "rich"

        embed.add_field(name=f'Flags correctly guessed:', value=f'{total}')
        sent_embed = await message.channel.send(embed=embed)


async def get_leaderboard(message, client):
    sent = await message.channel.send('Processing... (This may take a while!)')
    with open('modules/scores.json') as f:
        db = json.load(f)

    temp = []
    temp2 = []
    temp3 = []

    t = time.time()

    a = None
    for u, _ in db.items():
        a = u

    for user, d in db.items():
        print(f"{user}:%.2f seconds (%.3f minutes)" % (((time.time() - t), (time.time() - t) / 60)))
        if user == a:  # without this the command can take 10 times longer for some reason
            break
        name = str(await username_from_mention(user, client))[:-5]
        temp.append([d['flag']['total'], name])
        try:
            temp3.append([d['flag']['rounds_won'], name])
        except:
            continue
        try:
            temp2.append([d['flag']['games_won'], name])
        except:
            continue
        # print(f'{user} is here')


    print("\nMade lists in in %.2f seconds (%.3f minutes)" % (((time.time() - t), (time.time() - t) / 60)))
    t = time.time()

    # print('this is before sorting')

    temp.sort(key=lambda y: y[0], reverse=True)
    temp2.sort(key=lambda y: y[0], reverse=True)
    temp3.sort(key=lambda y: y[0], reverse=True)

    # print('this is after sorting')

    embed = discord.Embed(title=f"Global Leaderboard")
    embed.set_footer(
        text=f"Stat collection started 3/23/2021")
    embed.colour = discord.Colour.gold()
    embed.type = "rich"

    str_ = ""
    for total, name in temp[:10]:
        str_ += f"{name}: {total}\n"
    embed.add_field(name="__Total Flags__", value=str_)

    str_ = ""
    for total, name in temp3[:10]:
        str_ += f"{name}: {total}\n"
    embed.add_field(name="__Flag Rounds Won__", value=str_)

    str_ = ""
    for total, name in temp2[:10]:
        str_ += f"{name}: {total}\n"
    embed.add_field(name="__Flag Games Won__", value=str_)

    # print("\nSorted and added to embed in in %.5f seconds (%.3f minutes)" % (((time.time() - t), (time.time() - t) / 60)))

    await sent.delete()

    sent_embed = await message.channel.send(embed=embed)


def increment_user(user_mention, game_played: str, **kwargs):
    # kwargs will contain any information important to the game
    # game_played MUST be one of 'color', 'flag', or 'geography'
    GAMES = ['color', 'flag', 'geography']
    if game_played not in GAMES:
        print('u messed up mikey')
        return

    user_mention = str(user_mention).replace("!", "")

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
                try:
                    df[user_mention][game_played][key] += value
                except KeyError:
                    df[user_mention][game_played][key] = value
            else:
                df[user_mention][game_played][key] = value
                print("! not int or string")

    with open('modules/scores.json', 'w') as f:  # likely to cause issues! race condition
        json.dump(df, f, indent=4)

