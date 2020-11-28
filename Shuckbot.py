import logging
from datetime import datetime

import discord

from modules import tags, imagesearch, metar, imagefun, help, save, cleverbot, games

with open("keys.txt", "r") as file:  # file format: google key, owner ID, avwx key, bot client key on separate lines
    lines = file.read().splitlines()
    googleKey = lines[0]
    ownerID = int(lines[1])
    avwxKey = lines[2]
    clientKey = lines[3]

imagesearch.init(googleKey)
logging.basicConfig(level=logging.INFO)

defaultPrefix = ';'

client = discord.Client()


@client.event
async def on_message(message):
    if message.clean_content.startswith(';') and not message.author.bot and \
            len(message.clean_content) > 1:  # prefixes.search(q.guild == message.guild.id)[0]['prefix'])

        content = message.clean_content[1:]  # remove prefix

        # if content.lower().startswith("prefix"):
        #     if not message.author.permissions_in(message.channel).manage_roles:
        #         await message.channel.send("You must have the **Manage Roles** permission to do that.")
        #     elif len(content) < 8 or content[7] == ' ':
        #         await message.channel.send("Enter a character to set the prefix to.")
        #     elif len(content) > 8:
        #         await message.channel.send("Only enter one character to set the prefix to.")
        #     else:
        #         prefixes.update({'prefix': content[7]}, q.guild == message.guild.id)
        #         await message.channel.send("Prefix changed to " + content[7] + '.')

        if content.lower().startswith("ping"):
            now = datetime.now()
            sent = await message.channel.send("Measuring ping...")
            diff = sent.created_at - now
            await sent.edit(content="Pong! Shuckbot's ping is **" + str(int(diff.microseconds / 1000)) + "**ms.")

        elif content.lower().startswith(("help", "page")):
            await help.show_help(message, client, ownerID)

        elif content.lower().startswith(("img ", "i ", "im ")):
            await imagesearch.google_search(message)

        elif content.lower().startswith("r34"):
            await imagesearch.r34_search(message)

        elif content.lower().startswith(("pb", "picturebook", "photobook")):
            if ' ' not in content:
                await save.get_saved(message)

            else:
                arg = content.split(' ')[1].lower()  # the first argument

                if arg == 'add' or arg == 'save':
                    await save.save(message)

                elif arg == 'remove' or arg == "delete" or arg == "rm":
                    await save.remove(message, ownerID)

        elif content.lower().startswith(("tag", "t ")):
            if ' ' not in message.clean_content:
                await tags.syntax_error(message)
            else:
                arg = content.split(' ')[1].lower()  # the first argument

                if arg == 'add':
                    await tags.add(message)

                elif arg == 'remove' or arg == "delete":
                    await tags.remove(message, ownerID)

                elif arg == 'edit':
                    await tags.edit(message, ownerID)

                elif arg == 'owner':
                    args = message.clean_content.split(' ')
                    tag_owner = client.get_user(tags.owner(message))
                    if tag_owner == 0:
                        await message.channel.send("Tag **" + args[2] + "** does not exist")
                    else:
                        await message.channel.send("Tag **" + args[2] + "** is owned by `" + str(tag_owner) + "`")

                elif arg == 'list':
                    await tags.owned(message)

                elif arg == 'random':
                    await tags.get_random(message)

                else:
                    await tags.get(message)

        elif content.lower().startswith("metar"):
            await metar.metar(message, avwxKey)

        elif content.lower().startswith(("holding", "hold")):
            await imagefun.holding_imagemaker(message)

        elif content.lower().startswith(("exm", "exmilitary")):
            await imagefun.exmilitary_imagemaker(message)

        elif content.lower().startswith(("fantano", "fan", "review", "tnd")):
            await imagefun.fantano_imagemaker(message)

        elif content.lower().startswith(("1bit", "one", "1bit\n", "one\n", "1", "1\n")):
            await imagefun.one_imagemaker(message)

        elif content.lower().startswith("kim"):
            await imagefun.kim_imagemaker(message)

        elif content.lower().startswith(("e ", "emote")):
            await imagefun.get_emoji(message, client)

        elif content.lower().startswith(("sort", "pixelsort", "sortpixels")):
            await imagefun.sort_pixels(message)

        elif content.lower().startswith(("shuffle", "pixelshuffle")):
            await imagefun.pixel_shuffle(message)

        elif content.lower().startswith(("resize", "scale")):
            await imagefun.resize_img(message)

        elif content.lower().startswith("size"):
            await imagefun.get_size(message)

        elif content.lower().startswith(("twice", "mina")):
            await imagefun.twice_imagemaker(message)

        elif content.lower().startswith(("draw", "drawing")):
            await imagefun.drawing_imagemaker(message)

        elif content.lower().startswith("undo"):
            await imagefun.undo_img(message)

        elif content.lower().startswith(("heejin", "loona")):
            await imagefun.heejin_imagemaker(message)

        elif content.lower().startswith("school"):
            await imagefun.school_imagemaker(message)

        elif content.lower().startswith(("lecture", "lect")):
            await imagefun.lecture_imagemaker(message)

        elif content.lower().startswith("tesla"):
            await imagefun.tesla_imagemaker(message)

        elif content.lower().startswith("osu"):
            await imagefun.osu_imagemaker(message)

        elif content.lower().startswith(("color", "colour", "c ")):
            await imagefun.get_colour_from_hex(message)

        elif content.lower().startswith(("mix", "noisy")):
            await imagefun.mixer(message)

        elif content.lower().startswith("noise"):
            await imagefun.noise_imagemaker(message)

        elif content.lower().startswith(("mokou", "gf")):
            await imagefun.mokou_imagemaker(message)

        elif content.lower().startswith(("shift")):
            await imagefun.image_shift(message)

        elif content.lower().startswith(("megumin", "megu")):
            await imagefun.megumin_imagemaker(message)

        elif content.lower().startswith(("weezer")):
            await imagefun.weezer_imagemaker(message)

        elif content.lower().startswith(("game")):
            await games.game(message, client)

        elif content.lower().startswith(("rgb", "torgb", "2rgb")):
            await imagefun.to_rgb(message)

        elif content.lower().startswith(("a", "avatar")):
            await imagefun.get_avatar(message)

        elif content.lower().startswith(("purple")):
            await imagefun.purple(message)

        elif content.lower().startswith(("whatifitwaspurple")):
            await imagefun.whatifitwaspurple(message)

    if message.clean_content.lower() == "b" or message.clean_content.lower() == "n":
        await imagesearch.advance(message)

    if message.clean_content.lower().startswith("p"):
        await imagesearch.jump(message)

    if message.clean_content.lower() == "s":
        await imagesearch.stop(message)

    if message.clean_content.lower() == "based":
        await message.channel.send("certified based")

    if message.clean_content.startswith("@" + message.guild.get_member(client.user.id).display_name):
        await message.channel.send(
            cleverbot.cleverbot_message(message, message.guild.get_member(client.user.id).display_name))


client.run(clientKey)
