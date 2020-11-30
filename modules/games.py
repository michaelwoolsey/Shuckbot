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
    elif args[0] in ("colour"):
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
        elif args[1] in ("extreme", "x", "4"):
            await flag_guesser(message, client, 4)
        else:
            await flag_guesser(message, client)


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
    msg = None
    try:
        img = Image.new("RGB", (size, size), ImageColor.getcolor(('#' + col), "RGB"))
    except ValueError:
        await message.channel.send("Value Error has been thrown!")
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
            + " got " + str(int(np.ceil(winner[2]))) + "/100 points\n"
            , file=discord.File("clrguessresult.png"))
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

flags = [
{"name": ("Australia"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/australia/flag-800.png"},
{"name": ("Austria"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/austria/flag-800.png"},
{"name": ("Belgium"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/belgium/flag-800.png"},
{"name": ("Brazil"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/brazil/flag-800.png"},
{"name": ("Canada"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/canada/flag-800.png"},
{"name": ("China"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/china/flag-800.png"},
{"name": ("Czech Republic","Czechia"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/czech-republic/flag-800.png"},
{"name": ("Denmark"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/denmark/flag-800.png"},
{"name": ("Finland"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/finland/flag-800.png"},
{"name": ("France"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/france/flag-800.png"},
{"name": ("Germany"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/germany/flag-800.png"},
{"name": ("Iceland"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/iceland/flag-800.png"},
{"name": ("India"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/india/flag-800.png"},
{"name": ("Ireland"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/ireland/flag-800.png"},
{"name": ("Israel"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/israel/flag-800.png"},
{"name": ("Italy"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/italy/flag-800.png"},
{"name": ("Japan"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/japan/flag-800.png"},
{"name": ("Mexico"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/mexico/flag-800.png"},
{"name": ("Netherlands"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/netherlands/flag-800.png"},
{"name": ("New Zealand"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/new-zealand/flag-800.png"},
{"name": ("Norway"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/norway/flag-800.png"},
{"name": ("Poland"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/poland/flag-800.png"},
{"name": ("Portugal"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/portugal/flag-800.png"},
{"name": ("South Korea","Republic of Korea"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/south-korea/flag-800.png"},
{"name": ("Russia","Russian Federation"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/russia/flag-800.png"},
{"name": ("South Africa"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/south-africa/flag-800.png"},
{"name": ("Spain"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/spain/flag-800.png"},
{"name": ("Sweden"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/sweden/flag-800.png"},
{"name": ("Switzerland"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/switzerland/flag-800.png"},
{"name": ("Turkey"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/turkey/flag-800.png"},
{"name": ("Ukraine"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/ukraine/flag-800.png"},
{"name": ("The United Kingdom","United Kingdom","United Kingdom of Great Britain and Northern Ireland","The UK","UK"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/united-kingdom/flag-800.png"},
{"name": ("The United States","United States","United States of America","the United States of America","the US","USA","the USA","US"), "difficulty": 1, "url": "https://cdn.countryflags.com/thumbs/united-states-of-america/flag-800.png"},
{"name": ("Albania"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/albania/flag-800.png"},
{"name": ("Algeria"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/algeria/flag-800.png"},
{"name": ("Argentina"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/argentina/flag-800.png"},
{"name": ("Bangladesh"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/bangladesh/flag-800.png"},
{"name": ("Bosnia and Herzegovina"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/bosnia-and-herzegovina/flag-800.png"},
{"name": ("Botswana"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/botswana/flag-800.png"},
{"name": ("Cambodia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/cambodia/flag-800.png"},
{"name": ("Chile"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/chile/flag-800.png"},
{"name": ("Colombia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/colombia/flag-800.png"},
{"name": ("Costa Rica"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/costa-rica/flag-800.png"},
{"name": ("Croatia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/croatia/flag-800.png"},
{"name": ("Cuba"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/cuba/flag-800.png"},
{"name": ("Cyprus"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/cyprus/flag-800.png"},
{"name": ("North Korea","Democratic People's Republic of Korea"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/north-korea/flag-800.png"},
{"name": ("Egypt"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/egypt/flag-800.png"},
{"name": ("Estonia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/estonia/flag-800.png"},
{"name": ("Ethiopia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/ethiopia/flag-800.png"},
{"name": ("Greece"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/greece/flag-800.png"},
{"name": ("Honduras"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/honduras/flag-800.png"},
{"name": ("Hungary"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/hungary/flag-800.png"},
{"name": ("Iran"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/iran/flag-800.png"},
{"name": ("Iraq"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/iraq/flag-800.png"},
{"name": ("Indonesia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/indonesia/flag-800.png"},
{"name": ("Jamaica"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/jamaica/flag-800.png"},
{"name": ("Kenya"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/kenya/flag-800.png"},
{"name": ("Kuwait"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/kuwait/flag-800.png"},
{"name": ("Laos","Lao"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/laos/flag-800.png"},
{"name": ("Latvia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/latvia/flag-800.png"},
{"name": ("Lebanon"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/lebanon/flag-800.png"},
{"name": ("Liberia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/liberia/flag-800.png"},
{"name": ("Liechtenstein"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/liechtenstein/flag-800.png"},
{"name": ("Lithuania"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/lithuania/flag-800.png"},
{"name": ("Luxembourg"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/luxembourg/flag-800.png"},
{"name": ("Malaysia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/malaysia/flag-800.png"},
{"name": ("Monaco"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/monaco/flag-800.png"},
{"name": ("Morocco"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/morocco/flag-800.png"},
{"name": ("Myanmar"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/myanmar/flag-800.png"},
{"name": ("Namibia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/namibia/flag-800.png"},
{"name": ("Nepal"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/nepal/flag-800.png"},
{"name": ("Nicaragua"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/nicaragua/flag-800.png"},
{"name": ("Niger"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/niger/flag-800.png"},
{"name": ("Nigeria"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/nigeria/flag-800.png"},
{"name": ("North Macedonia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/north-macedonia/flag-800.png"},
{"name": ("Oman"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/oman/flag-800.png"},
{"name": ("Pakistan"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/pakistan/flag-800.png"},
{"name": ("Panama"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/panama/flag-800.png"},
{"name": ("Papua New Guinea"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/papua-new-guinea/flag-800.png"},
{"name": ("Peru"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/peru/flag-800.png"},
{"name": ("Philippines"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/philippines/flag-800.png"},
{"name": ("Qatar"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/qatar/flag-800.png"},
{"name": ("Moldova"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/moldova/flag-800.png"},
{"name": ("Romania"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/romania/flag-800.png"},
{"name": ("Rwanda"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/rwanda/flag-800.png"},
{"name": ("Saudi Arabia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/saudi-arabia/flag-800.png"},
{"name": ("Serbia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/serbia/flag-800.png"},
{"name": ("Seychelles"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/seychelles/flag-800.png"},
{"name": ("Singapore"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/singapore/flag-800.png"},
{"name": ("Slovakia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/slovakia/flag-800.png"},
{"name": ("Slovenia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/slovenia/flag-800.png"},
{"name": ("Somalia"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/somalia/flag-800.png"},
{"name": ("Sri Lanka"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/sri-lanka/flag-800.png"},
{"name": ("Syria"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/syria/flag-800.png"},
{"name": ("Thailand"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/thailand/flag-800.png"},
{"name": ("Uganda"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/uganda/flag-800.png"},
{"name": ("United Arab Emirates","UAE"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/united-arab-emirates/flag-800.png"},
{"name": ("Uruguay"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/uruguay/flag-800.png"},
{"name": ("Venezuela"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/venezuela/flag-800.png"},
{"name": ("Vatican City"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/vatican-city/flag-800.png"},
{"name": ("Vietnam","Viet Nam"), "difficulty": 2, "url": "https://cdn.countryflags.com/thumbs/vietnam/flag-800.png"},
{"name": ("Afghanistan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/afghanistan/flag-800.png"},
{"name": ("Andorra"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/andorra/flag-800.png"},
{"name": ("Angola"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/angola/flag-800.png"},
{"name": ("Antigua"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/antigua/flag-800.png"},
{"name": ("Armenia"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/armenia/flag-800.png"},
{"name": ("Azerbaijan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/azerbaijan/flag-800.png"},
{"name": ("The Bahamas","Bahamas"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/bahamas/flag-800.png"},
{"name": ("Bahrain"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/bahrain/flag-800.png"},
{"name": ("Barbados"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/barbados/flag-800.png"},
{"name": ("Belarus"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/belarus/flag-800.png"},
{"name": ("Belize"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/belize/flag-800.png"},
{"name": ("Benin"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/benin/flag-800.png"},
{"name": ("Bhutan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/bhutan/flag-800.png"},
{"name": ("Bolivia"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/bolivia/flag-800.png"},
{"name": ("Brunei"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/brunei/flag-800.png"},
{"name": ("Bulgaria"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/bulgaria/flag-800.png"},
{"name": ("Burkina Faso"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/burkina-faso/flag-800.png"},
{"name": ("Burundi"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/burundi/flag-800.png"},
{"name": ("Cape Verde","Cabo Verde"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/cape-verde/flag-800.png"},
{"name": ("Cameroon"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/cameroon/flag-800.png"},
{"name": ("Central African Republic","CAR"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/central-african-republic/flag-800.png"},
{"name": ("Chad"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/chad/flag-800.png"},
{"name": ("Comoros"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/comoros/flag-800.png"},
{"name": ("Republic of the Congo","Republic of Congo","Congo Republic"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/congo-republic-of-the/flag-800.png"},
{"name": ("Ivory Coast","Côte d'Ivoire","Cote d'Ivoire"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/cote-d-ivoire/flag-800.png"},
{"name": ("Democratic Republic of the Congo","the Congo","Congo"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/congo-democratic-republic-of-the/flag-800.png"},
{"name": ("Djibouti"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/djibouti/flag-800.png"},
{"name": ("Dominica"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/dominica/flag-800.png"},
{"name": ("Dominican Republic","the Dominican Republic"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/dominican-republic/flag-800.png"},
{"name": ("Ecuador"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/ecuador/flag-800.png"},
{"name": ("El Salvador"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/el-salvador/flag-800.png"},
{"name": ("Equatorial Guinea"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/equatorial-guinea/flag-800.png"},
{"name": ("Eritrea"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/eritrea/flag-800.png"},
{"name": ("Eswatini"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/eswatini/flag-800.png"},
{"name": ("Fiji"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/fiji/flag-800.png"},
{"name": ("Gabon"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/gabon/flag-800.png"},
{"name": ("The Gambia","Gambia"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/gambia/flag-800.png"},
{"name": ("Georgia"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/georgia/flag-800.png"},
{"name": ("Ghana"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/ghana/flag-800.png"},
{"name": ("Grenada"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/grenada/flag-800.png"},
{"name": ("Guatemala"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/guatemala/flag-800.png"},
{"name": ("Guinea"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/guinea/flag-800.png"},
{"name": ("Guinea-Bissau","Guinea Bissau"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/guinea-bissau/flag-800.png"},
{"name": ("Guyana"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/guyana/flag-800.png"},
{"name": ("Haiti"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/haiti/flag-800.png"},
{"name": ("Jordan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/jordan/flag-800.png"},
{"name": ("Kazakhstan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/kazakhstan/flag-800.png"},
{"name": ("Kiribati"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/kiribati/flag-800.png"},
{"name": ("Kyrgyzstan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/kyrgyzstan/flag-800.png"},
{"name": ("Lesotho"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/lesotho/flag-800.png"},
{"name": ("Libya"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/libya/flag-800.png"},
{"name": ("Madagascar"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/madagascar/flag-800.png"},
{"name": ("Malawi"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/malawi/flag-800.png"},
{"name": ("Maldives"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/maldives/flag-800.png"},
{"name": ("Mali"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/mali/flag-800.png"},
{"name": ("Malta"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/malta/flag-800.png"},
{"name": ("Marshall Islands"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/marshall-islands/flag-800.png"},
{"name": ("Mauritania"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/mauritania/flag-800.png"},
{"name": ("Mauritius"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/mauritius/flag-800.png"},
{"name": ("Federated States of Micronesia","Micronesia"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/micronesia/flag-800.png"},
{"name": ("Mongolia"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/mongolia/flag-800.png"},
{"name": ("Montenegro"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/montenegro/flag-800.png"},
{"name": ("Mozambique"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/mozambique/flag-800.png"},
{"name": ("Nauru"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/nauru/flag-800.png"},
{"name": ("Palau"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/palau/flag-800.png"},
{"name": ("Paraguay"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/paraguay/flag-800.png"},
{"name": ("Saint Kitts and Nevis","St. Kitts and Nevis"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/saint-kitts-and-nevis/flag-800.png"},
{"name": ("Saint Lucia","St. Lucia"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/saint-lucia/flag-800.png"},
{"name": ("Saint Vincent and the Grenadines","St. Vincent and the Grenadines"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/saint-vincent-and-the-grenadines/flag-800.png"},
{"name": ("Samoa"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/samoa/flag-800.png"},
{"name": ("San Marino"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/san-marino/flag-800.png"},
{"name": ("São Tomé and Príncipe","Sao Tome and Principe"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/sao-tome-and-principe/flag-800.png"},
{"name": ("Senegal"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/senegal/flag-800.png"},
{"name": ("Sierra Leone"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/sierra-leone/flag-800.png"},
{"name": ("Solomon Islands"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/solomon-islands/flag-800.png"},
{"name": ("South Sudan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/south-sudan/flag-800.png"},
{"name": ("Sudan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/sudan/flag-800.png"},
{"name": ("Suriname"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/suriname/flag-800.png"},
{"name": ("Tajikistan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/tajikistan/flag-800.png"},
{"name": ("East Timor","Timor-Leste"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/east-timor/flag-800.png"},
{"name": ("Togo"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/togo/flag-800.png"},
{"name": ("Tonga"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/tonga/flag-800.png"},
{"name": ("Trinidad and Tobago"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/trinidad-and-tobago/flag-800.png"},
{"name": ("Tunisia"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/tunisia/flag-800.png"},
{"name": ("Turkmenistan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/turkmenistan/flag-800.png"},
{"name": ("Tuvalu"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/tuvalu/flag-800.png"},
{"name": ("Tanzania","United Republic of Tanzania"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/tanzania/flag-800.png"},
{"name": ("Uzbekistan"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/uzbekistan/flag-800.png"},
{"name": ("Vanuatu"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/vanuatu/flag-800.png"},
{"name": ("Yemen"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/yemen/flag-800.png"},
{"name": ("Zambia"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/zambia/flag-800.png"},
{"name": ("Zimbabwe"), "difficulty": 3, "url": "https://cdn.countryflags.com/thumbs/zimbabwe/flag-800.png"},
]


async def flag_guesser(message, client, difficulty=0):
    lengths = [0, 0, 0]
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
    else:
        max_index = lengths[0] + lengths[1] + lengths[2]

    country_index = random.randint(min_index, max_index)

    # country_index = 30

    response = requests.get(flags[country_index]["url"])
    flag_img = Image.open(BytesIO(response.content))
    flag_img.save("flag.png")

    embed = discord.Embed(title="You have " + str(game_time) + " seconds to guess the flag!")
    embed.colour = discord.Color.gold()
    embed.type = "rich"

    embed.set_image(url="attachment://flag.png")
    await message.channel.send(embed=embed, file=discord.File("flag.png"))
    # await message.channel.send("You have " + str(game_time) + " seconds to guess the flag!", file=discord.File("flag.png"))

    def check(m):
        if type(flags[country_index]["name"]) is tuple:
            for n in flags[country_index]["name"]:
                if n.lower() == m.content.lower() and m.channel == message.channel:
                    return True
            return False
        return m.channel == message.channel and (m.content.lower() in flags[country_index]["name"].lower())

    t = time.time()
    try:
        msg = await client.wait_for('message', check=check, timeout=game_time)
    except:
        try:
            await message.channel.send("Sorry, nobody got the flag correct! The correct answer was: " + flags[country_index]["name"])
        except TypeError:
            await message.channel.send("Sorry, nobody got the flag correct! The correct answer was: " + flags[country_index]["name"][0])
        return
    try:
        await message.channel.send("Good job " + msg.author.mention + "! The country was " + flags[country_index]['name'])
    except TypeError:
        await message.channel.send("Good job " + msg.author.mention + "! The country was " + flags[country_index]['name'][0])









# difference = abs(actual_r - r) + abs(actual_g - g) + abs(actual_b - b)

# a = 0.39
# f = 1.05
# g = 0.14
# h = 26
# x = difference
# # score = max((-100*np.e**(a*(difference+b)))/(np.e**a*(difference+b) + 100) + 102.85 - c*np.sqrt(difference), 0)
# score = np.ceil(max(((-100 * np.e**(a*x))/(np.e**(a*x)+120)+100.75),
# 					(((-100 * np.e**(g*(x+h)))/(np.e**(g*(x+h))+120) + 100)/f)))
# score = 0 if x > 60 else score

# scale = 0.045
# score = np.ceil((-100 * np.e ** (scale * difference)) / (np.e ** (scale * difference) + 120) + 100)
# res = (100 - (difference - 2)**0.8 * (11 / 3)) if difference > 2 else 100
# res = (100 - difference * (1 + 2/3)) if difference > 2 else 100
# if difference > 400:
# 	score = 0




# easy_flags = [
# {"name": ("Australia"), "difficulty": 1, "url": ""},
# {"name": ("Austria"), "difficulty": 1, "url": ""},
# {"name": ("Belgium"), "difficulty": 1, "url": ""},
# {"name": ("Brazil"), "difficulty": 1, "url": ""},
# {"name": ("Canada"), "difficulty": 1, "url": ""},
# {"name": ("China"), "difficulty": 1, "url": ""},
# {"name": ("Denmark"), "difficulty": 1, "url": ""},
# {"name": ("Finland"), "difficulty": 1, "url": ""},
# {"name": ("France"), "difficulty": 1, "url": ""},
# {"name": ("Germany"), "difficulty": 1, "url": ""},
# {"name": ("Iceland"), "difficulty": 1, "url": ""},
# {"name": ("India"), "difficulty": 1, "url": ""},
# {"name": ("Indonesia"), "difficulty": 1, "url": ""},
# {"name": ("Republic of Ireland","Ireland"), "difficulty": 1, "url": ""},
# {"name": ("Israel"), "difficulty": 1, "url": ""},
# {"name": ("Italy"), "difficulty": 1, "url": ""},
# {"name": ("Japan"), "difficulty": 1, "url": ""},
# {"name": ("Mexico"), "difficulty": 1, "url": ""},
# {"name": ("Kingdom of the Netherlands","Netherlands"), "difficulty": 1, "url": ""},
# {"name": ("New Zealand"), "difficulty": 1, "url": ""},
# {"name": ("Norway"), "difficulty": 1, "url": ""},
# {"name": ("Poland"), "difficulty": 1, "url": ""},
# {"name": ("Portugal"), "difficulty": 1, "url": ""},
# {"name": ("South Korea","Republic of Korea"), "difficulty": 1, "url": ""},
# {"name": ("Russia","Russian Federation"), "difficulty": 1, "url": ""},
# {"name": ("South Africa"), "difficulty": 1, "url": ""},
# {"name": ("Spain"), "difficulty": 1, "url": ""},
# {"name": ("Sweden"), "difficulty": 1, "url": ""},
# {"name": ("Switzerland"), "difficulty": 1, "url": ""},
# {"name": ("Turkey"), "difficulty": 1, "url": ""},
# {"name": ("Ukraine"), "difficulty": 1, "url": ""},
# {"name": ("United Kingdom","United Kingdom of Great Britain and Northern Ireland","The UK","UK"), "difficulty": 1, "url": ""},
# {"name": ("The United States","United States","United States of America","the United States of America","the US","USA","the USA","US"), "difficulty": 1, "url": ""}
# ]
#
# normal_flags = [
# {"name": ("Albania"), "difficulty": 2, "url": ""},
# {"name": ("Algeria"), "difficulty": 2, "url": ""},
# {"name": ("Argentina"), "difficulty": 2, "url": ""},
# {"name": ("Bangladesh"), "difficulty": 2, "url": ""},
# {"name": ("Bosnia and Herzegovina"), "difficulty": 2, "url": ""},
# {"name": ("Botswana"), "difficulty": 2, "url": ""},
# {"name": ("Cambodia"), "difficulty": 2, "url": ""},
# {"name": ("Chile"), "difficulty": 2, "url": ""},
# {"name": ("Colombia"), "difficulty": 2, "url": ""},
# {"name": ("Costa Rica"), "difficulty": 2, "url": ""},
# {"name": ("Croatia"), "difficulty": 2, "url": ""},
# {"name": ("Cuba"), "difficulty": 2, "url": ""},
# {"name": ("Cyprus"), "difficulty": 2, "url": ""},
# {"name": ("Czech Republic","Czechia"), "difficulty": 2, "url": ""},
# {"name": ("North Korea","Democratic People's Republic of Korea"), "difficulty": 2, "url": ""},
# {"name": ("Egypt"), "difficulty": 2, "url": ""},
# {"name": ("Estonia"), "difficulty": 2, "url": ""},
# {"name": ("Ethiopia"), "difficulty": 2, "url": ""},
# {"name": ("Greece"), "difficulty": 2, "url": ""},
# {"name": ("Honduras"), "difficulty": 2, "url": ""},
# {"name": ("Hungary"), "difficulty": 2, "url": ""},
# {"name": ("Iran"), "difficulty": 2, "url": ""},
# {"name": ("Iraq"), "difficulty": 2, "url": ""},
# {"name": ("Jamaica"), "difficulty": 2, "url": ""},
# {"name": ("Kenya"), "difficulty": 2, "url": ""},
# {"name": ("Kuwait"), "difficulty": 2, "url": ""},
# {"name": ("Latvia"), "difficulty": 2, "url": ""},
# {"name": ("Lebanon"), "difficulty": 2, "url": ""},
# {"name": ("Liberia"), "difficulty": 2, "url": ""},
# {"name": ("Liechtenstein"), "difficulty": 2, "url": ""},
# {"name": ("Lithuania"), "difficulty": 2, "url": ""},
# {"name": ("Luxembourg"), "difficulty": 2, "url": ""},
# {"name": ("Malaysia"), "difficulty": 2, "url": ""},
# {"name": ("Monaco"), "difficulty": 2, "url": ""},
# {"name": ("Morocco"), "difficulty": 2, "url": ""},
# {"name": ("Myanmar"), "difficulty": 2, "url": ""},
# {"name": ("Namibia"), "difficulty": 2, "url": ""},
# {"name": ("Nauru"), "difficulty": 2, "url": ""},
# {"name": ("Nepal"), "difficulty": 2, "url": ""},
# {"name": ("Nicaragua"), "difficulty": 2, "url": ""},
# {"name": ("Niger"), "difficulty": 2, "url": ""},
# {"name": ("Nigeria"), "difficulty": 2, "url": ""},
# {"name": ("North Macedonia"), "difficulty": 2, "url": ""},
# {"name": ("Oman"), "difficulty": 2, "url": ""},
# {"name": ("Pakistan"), "difficulty": 2, "url": ""},
# {"name": ("Panama"), "difficulty": 2, "url": ""},
# {"name": ("Papua New Guinea"), "difficulty": 2, "url": ""},
# {"name": ("Peru"), "difficulty": 2, "url": ""},
# {"name": ("Philippines"), "difficulty": 2, "url": ""},
# {"name": ("Qatar"), "difficulty": 2, "url": ""},
# {"name": ("Moldova"), "difficulty": 2, "url": ""},
# {"name": ("Romania"), "difficulty": 2, "url": ""},
# {"name": ("Rwanda"), "difficulty": 2, "url": ""},
# {"name": ("Saudi Arabia"), "difficulty": 2, "url": ""},
# {"name": ("Serbia"), "difficulty": 2, "url": ""},
# {"name": ("Seychelles"), "difficulty": 2, "url": ""},
# {"name": ("Singapore"), "difficulty": 2, "url": ""},
# {"name": ("Slovakia"), "difficulty": 2, "url": ""},
# {"name": ("Slovenia"), "difficulty": 2, "url": ""},
# {"name": ("Somalia"), "difficulty": 2, "url": ""},
# {"name": ("Sri Lanka"), "difficulty": 2, "url": ""},
# {"name": ("Syria"), "difficulty": 2, "url": ""},
# {"name": ("Thailand"), "difficulty": 2, "url": ""},
# {"name": ("Uganda"), "difficulty": 2, "url": ""},
# {"name": ("United Arab Emirates","UAE"), "difficulty": 2, "url": ""},
# {"name": ("Uruguay"), "difficulty": 2, "url": ""},
# {"name": ("Venezuela"), "difficulty": 2, "url": ""},
# {"name": ("Vietnam","Viet Nam"), "difficulty": 2, "url": ""},
# ]
#
# hard_flags = [
# {"name": ("Afghanistan"), "difficulty": 3, "url": ""},
# {"name": ("Andorra"), "difficulty": 3, "url": ""},
# {"name": ("Angola"), "difficulty": 3, "url": ""},
# {"name": ("Antigua"), "difficulty": 3, "url": ""},
# {"name": ("Armenia"), "difficulty": 3, "url": ""},
# {"name": ("Azerbaijan"), "difficulty": 3, "url": ""},
# {"name": ("The Bahamas","Bahamas"), "difficulty": 3, "url": ""},
# {"name": ("Bahrain"), "difficulty": 3, "url": ""},
# {"name": ("Barbados"), "difficulty": 3, "url": ""},
# {"name": ("Belarus"), "difficulty": 3, "url": ""},
# {"name": ("Belize"), "difficulty": 3, "url": ""},
# {"name": ("Benin"), "difficulty": 3, "url": ""},
# {"name": ("Bhutan"), "difficulty": 3, "url": ""},
# {"name": ("Bolivia"), "difficulty": 3, "url": ""},
# {"name": ("Brunei"), "difficulty": 3, "url": ""},
# {"name": ("Bulgaria"), "difficulty": 3, "url": ""},
# {"name": ("Burkina Faso"), "difficulty": 3, "url": ""},
# {"name": ("Burundi"), "difficulty": 3, "url": ""},
# {"name": ("Cape Verde","Cabo Verde"), "difficulty": 3, "url": ""},
# {"name": ("Cameroon"), "difficulty": 3, "url": ""},
# {"name": ("Central African Republic","CAR"), "difficulty": 3, "url": ""},
# {"name": ("Chad"), "difficulty": 3, "url": ""},
# {"name": ("Comoros"), "difficulty": 3, "url": ""},
# {"name": ("Republic of the Congo","Republic of Congo","Congo Republic"), "difficulty": 3, "url": ""},
# {"name": ("Ivory Coast","Côte d'Ivoire","Cote d'Ivoire"), "difficulty": 3, "url": ""},
# {"name": ("Democratic Republic of the Congo","the Congo","Congo"), "difficulty": 3, "url": ""},
# {"name": ("Djibouti"), "difficulty": 3, "url": ""},
# {"name": ("Dominica"), "difficulty": 3, "url": ""},
# {"name": ("Dominican Republic","the Dominican Republic"), "difficulty": 3, "url": ""},
# {"name": ("Ecuador"), "difficulty": 3, "url": ""},
# {"name": ("El Salvador"), "difficulty": 3, "url": ""},
# {"name": ("Equatorial Guinea"), "difficulty": 3, "url": ""},
# {"name": ("Eritrea"), "difficulty": 3, "url": ""},
# {"name": ("Eswatini"), "difficulty": 3, "url": ""},
# {"name": ("Fiji"), "difficulty": 3, "url": ""},
# {"name": ("Gabon"), "difficulty": 3, "url": ""},
# {"name": ("The Gambia","Gambia"), "difficulty": 3, "url": ""},
# {"name": ("Georgia"), "difficulty": 3, "url": ""},
# {"name": ("Ghana"), "difficulty": 3, "url": ""},
# {"name": ("Grenada"), "difficulty": 3, "url": ""},
# {"name": ("Guatemala"), "difficulty": 3, "url": ""},
# {"name": ("Guinea"), "difficulty": 3, "url": ""},
# {"name": ("Guinea-Bissau","Guinea Bissau"), "difficulty": 3, "url": ""},
# {"name": ("Guyana"), "difficulty": 3, "url": ""},
# {"name": ("Haiti"), "difficulty": 3, "url": ""},
# {"name": ("Jordan"), "difficulty": 3, "url": ""},
# {"name": ("Kazakhstan"), "difficulty": 3, "url": ""},
# {"name": ("Kiribati"), "difficulty": 3, "url": ""},
# {"name": ("Kyrgyzstan"), "difficulty": 3, "url": ""},
# {"name": ("Laos","Lao"), "difficulty": 3, "url": ""},
# {"name": ("Lesotho"), "difficulty": 3, "url": ""},
# {"name": ("Libya"), "difficulty": 3, "url": ""},
# {"name": ("Madagascar"), "difficulty": 3, "url": ""},
# {"name": ("Malawi"), "difficulty": 3, "url": ""},
# {"name": ("Maldives"), "difficulty": 3, "url": ""},
# {"name": ("Mali"), "difficulty": 3, "url": ""},
# {"name": ("Malta"), "difficulty": 3, "url": ""},
# {"name": ("Marshall Islands"), "difficulty": 3, "url": ""},
# {"name": ("Mauritania"), "difficulty": 3, "url": ""},
# {"name": ("Mauritius"), "difficulty": 3, "url": ""},
# {"name": ("Federated States of Micronesia","Micronesia"), "difficulty": 3, "url": ""},
# {"name": ("Mongolia"), "difficulty": 3, "url": ""},
# {"name": ("Montenegro"), "difficulty": 3, "url": ""},
# {"name": ("Mozambique"), "difficulty": 3, "url": ""},
# {"name": ("Palau"), "difficulty": 3, "url": ""},
# {"name": ("Paraguay"), "difficulty": 3, "url": ""},
# {"name": ("Saint Kitts and Nevis","St. Kitts and Nevis"), "difficulty": 3, "url": ""},
# {"name": ("Saint Lucia","St. Lucia"), "difficulty": 3, "url": ""},
# {"name": ("Saint Vincent and the Grenadines","St. Vincent and the Grenadines"), "difficulty": 3, "url": ""},
# {"name": ("Samoa"), "difficulty": 3, "url": ""},
# {"name": ("San Marino"), "difficulty": 3, "url": ""},
# {"name": ("São Tomé and Príncipe","Sao Tome and Principe"), "difficulty": 3, "url": ""},
# {"name": ("Senegal"), "difficulty": 3, "url": ""},
# {"name": ("Sierra Leone"), "difficulty": 3, "url": ""},
# {"name": ("Solomon Islands"), "difficulty": 3, "url": ""},
# {"name": ("South Sudan"), "difficulty": 3, "url": ""},
# {"name": ("Sudan"), "difficulty": 3, "url": ""},
# {"name": ("Suriname"), "difficulty": 3, "url": ""},
# {"name": ("Tajikistan"), "difficulty": 3, "url": ""},
# {"name": ("East Timor","Timor-Leste"), "difficulty": 3, "url": ""},
# {"name": ("Togo"), "difficulty": 3, "url": ""},
# {"name": ("Tonga"), "difficulty": 3, "url": ""},
# {"name": ("Trinidad and Tobago"), "difficulty": 3, "url": ""},
# {"name": ("Tunisia"), "difficulty": 3, "url": ""},
# {"name": ("Turkmenistan"), "difficulty": 3, "url": ""},
# {"name": ("Tuvalu"), "difficulty": 3, "url": ""},
# {"name": ("Tanzania","United Republic of Tanzania"), "difficulty": 3, "url": ""},
# {"name": ("Uzbekistan"), "difficulty": 3, "url": ""},
# {"name": ("Vanuatu"), "difficulty": 3, "url": ""},
# {"name": ("Yemen"), "difficulty": 3, "url": ""},
# {"name": ("Zambia"), "difficulty": 3, "url": ""},
# {"name": ("Zimbabwe"), "difficulty": 3, "url": ""}
# ]
