import pprint

import discord
from tinydb import TinyDB, Query
from googleapiclient.discovery import build
from googleapiclient import errors
import logging

with open("keys.txt", "r") as file:  # file format: google key, owner ID, bot client key on separate lines
    lines = file.read().splitlines()
    googleKey = lines[0]
    ownerID = int(lines[1])
    clientKey = lines[2]

try:
    searchService = build('customsearch', 'v1', developerKey=googleKey)
except errors.HttpError:  # sometimes this happens for some reason
    print("Daily quota exceeded!")

logging.basicConfig(level=logging.INFO)

defaultPrefix = ';'
tags = TinyDB('tags.json')
commands = [
    # {'command': 'prefix <character>', 'info': "Changes the command prefix for the server"},
    {'command': 'i/im/img <query>', 'info': "Google image searches for an image"},
    {'command': 't/tag <tag> / t/tag add <tag> <content>', 'info': 'Access or add a tag'}
]

searches = [{}]

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

        if content.lower().startswith("help"):
            bill = client.get_user(ownerID)
            embed = discord.Embed()
            embed.title = "Shuckbot help"
            embed.type = "rich"
            embed.colour = discord.Color.gold()
            for item in commands:
                embed.add_field(name=item['command'], value=item['info'], inline=False)
            embed.set_footer(text="Shuckbot, by billofbong", icon_url=bill.avatar_url)
            await message.channel.send(embed=embed)

        if content.lower().startswith(("img", "i", "im")) and ' ' in content:
            try:
                query = content.split(' ', 1)[1]  # splits the img and the rest of the command
                res = searchService.cse().list(q=query,
                                               cx="017178301722928584583:yi4kptiqtbq",
                                               searchType="image").execute()
                embed = discord.Embed()
                embed.title = "Image Search for " + query
                embed.set_image(url=res['items'][0]['link']).set_footer(text="Page 1 of " + str(len(res['items']))) \
                    .set_author(name=message.author.display_name, icon_url=message.author.avatar_url)

                sent = await message.channel.send(embed=embed)  # save the message
                meta = {'chan': message.channel.id, 'msg': sent, 'res': res, 'pg': 1, 'author': message.author.id}  # store the message channel, the message to edit, the query results, the page we're on, and the author
                found = False  # is there a previous search in this channel
                if not searches[0]:
                    searches[0] = meta  # if there are no previous searches anywhere, make this one the first one
                    found = True
                else:
                    for i in range(len(searches)):
                        if searches[i]['chan'] == message.channel.id:
                            searches[i] = meta  # replace this channel's previous search with the new one
                            found = True
                if not found:
                    searches.append(meta)  # if there isn't a search in this channel, append it to the list
            except errors.HttpError:  # google returns a 403 when you're out of quota
                await message.channel.send("The daily quota for Google searches has been exceeded.")
            except NameError:  # sometimes build() fails when you're over quota instead of returning the 403 here
                await message.channel.send("The daily quota for Google searches has been exceeded.")

        if content.lower().startswith(("tag", "t")):
            if ' ' not in content:
                await message.channel.send("Syntax error\n```fix\ntag <tag>\ntag add <tag> <content>"
                                           "\ntag edit <tag> <content>\ntag remove <tag>\ntag owner <tag>```")
            else:
                arg = content.split(' ')[1].lower()  # the first argument
                args = content.split(' ', 3)  # (t)(add)(something)(everything else)

                if arg == 'add':
                    if len(args) < 4:
                        await message.channel.send("Syntax error\n`;tag add <tag> <content>`")
                    else:
                        result = tags.search(Query().tag == args[2].lower())
                        if not result:
                            tags.insert({'tag': args[2].lower(), 'content': args[3], 'owner': message.author.id})  # inserts as lower case
                            await message.channel.send("Added tag **" + args[2] + "**!")
                        else:
                            await message.channel.send("Tag **" + args[2] + "** already exists!")
                elif arg == 'edit' or arg == 'remove' or arg == "delete":
                    if len(args) < 3:
                        await message.channel.send("Syntax error\n`;tag edit/remove <tag> (<content>)`")
                    else:
                        result = tags.search(Query().tag == args[2].lower())
                        if not result:  # if result is not found
                            await message.channel.send("Tag **" + args[2] + "** not found!")
                        else:
                            if result[0]['owner'] == message.author.id or message.author.id == ownerID:  # the owner can delete tags
                                if arg == 'remove' or arg == 'delete':
                                    tags.remove(Query().tag == args[2].lower())
                                    await message.channel.send("Removed tag **" + args[2] + "**!")
                                elif arg == 'edit':
                                    if len(content.split(' ')) < 4:
                                        await message.channel.send("Syntax error\n`;tag edit <tag> <content>`")
                                    else:
                                        tags.update({'content': args[3]}, Query().tag == args[2].lower())
                                        await message.channel.send("Edited tag **" + args[2] + "**!")
                            else:
                                await message.channel.send("You are not the author of tag **" + args[2] + "**!")
                elif arg == 'owner':
                    result = tags.search(Query().tag == args[2].lower())
                    if not result:
                        await message.channel.send("Tag **" + args[2] + "** not found!")
                    else:
                        owner = client.get_user(result[0]['owner'])
                        await message.channel.send("Tag **" + args[2] + "** is owned by `" + str(owner) + "`")
                elif arg == 'list':
                    results = tags.search(Query().owner == message.author.id)
                    if not results:
                        await message.channel.send("You don't own any tags!")
                    else:
                        embed = discord.Embed()
                        embed.title = "Tag list"
                        embed.type = "rich"
                        embed.colour = discord.Color.gold()
                        to_send = ""
                        for i in range(len(results)):
                            to_send += str(i + 1) + ". " + results[i]['tag'][:1024] + "\n"
                        embed.add_field(name="Tags", value=to_send, inline=False)
                        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                        await message.channel.send(embed=embed)
                else:
                    result = tags.search(Query().tag == arg)
                    if not result:
                        await message.channel.send("Tag **" + args[1] + "** not found!")
                    else:
                        await message.channel.send(result[0]['content'])

    if message.clean_content.lower() == "b" or message.clean_content.lower() == "n" and searches[0]:
        for item in searches:
            if item['chan'] == message.channel.id and item['pg']:
                if item['author'] != message.author.id:
                    break
                embed = item['msg'].embeds[0]
                if message.clean_content.lower() == "b":  # reverse page unless it's page 10 in which case loop around
                    if item['pg'] > 1:
                        item['pg'] -= 1
                    else:
                        item['pg'] = 10
                else:  # same as b except go forwards
                    if item['pg'] < 10:
                        item['pg'] += 1
                    else:
                        item['pg'] = 1
                embed.set_image(url=item['res']['items'][item['pg'] - 1]['link']) \
                    .set_footer(text="Page " + str(item['pg']) + " of " + str(len(item['res']['items'])))  # replace the embed
                await item['msg'].edit(embed=embed)
                await message.delete()
                break


client.run(clientKey)
