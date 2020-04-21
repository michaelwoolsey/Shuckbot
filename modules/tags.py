from tinydb import TinyDB, Query
import discord

tagsDB = TinyDB('tags.json')


async def syntax_error(message):
    await message.channel.send("Syntax error\n```fix\ntag <tag>\ntag add <tag> <content>"
                               "\ntag edit <tag> <content>\ntag remove <tag>\ntag owner <tag>```")


async def add(message):
    args = message.clean_content.split(' ', 3)
    if len(args) < 4:
        await message.channel.send("Syntax error\n`;tag add <tag> <content>`")
    else:
        result = tagsDB.search(Query().tag == args[2].lower())
        if not result:
            tagsDB.insert(
                {'tag': args[2].lower(), 'content': args[3], 'owner': message.author.id})  # inserts as lower case
            await message.channel.send("Added tag **" + args[2] + "**!")
        else:
            await message.channel.send("Tag **" + args[2] + "** already exists!")


async def remove(message, owner_id):
    args = message.clean_content.split(' ', 3)
    if len(args) < 3:
        await message.channel.send("Syntax error\n`;tag remove <tag> (<content>)`")
    else:
        result = tagsDB.search(Query().tag == args[2].lower())
        if not result:  # if result is not found
            await message.channel.send("Tag **" + args[2] + "** not found!")
        else:
            if result[0]['owner'] == message.author.id or message.author.id == owner_id:  # the owner can delete tags
                tagsDB.remove(Query().tag == args[2].lower())
                await message.channel.send("Removed tag **" + args[2] + "**!")
            else:
                await message.channel.send("You are not the author of tag **" + args[2] + "**!")


async def edit(message, owner_id):
    args = message.clean_content.split(' ', 3)
    if len(args) < 3:
        await message.channel.send("Syntax error\n`;tag edit <tag> (<content>)`")
    else:
        result = tagsDB.search(Query().tag == args[2].lower())
        if not result:  # if result is not found
            await message.channel.send("Tag **" + args[2] + "** not found!")
        else:
            if result[0]['owner'] == message.author.id or message.author.id == owner_id:
                if len(message.clean_content.split(' ')) < 4:
                    await message.channel.send("Syntax error\n`;tag edit <tag> <content>`")
                else:
                    tagsDB.update({'content': args[3]}, Query().tag == args[2].lower())
                    await message.channel.send("Edited tag **" + args[2] + "**!")
            else:
                await message.channel.send("You are not the author of tag **" + args[2] + "**!")


# returns integer owner id, 0 if not found
def owner(message):
    args = message.clean_content.split(' ', 3)
    result = tagsDB.search(Query().tag == args[2].lower())
    if not result:
        return 0
    else:
        return result[0]['owner']


async def owned(message):
    results = tagsDB.search(Query().owner == message.author.id)
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


async def get(message):
    args = message.clean_content.split(' ', 3)
    result = tagsDB.search(Query().tag == args[1].lower())
    if not result:
        await message.channel.send("Tag **" + args[1] + "** not found!")
    else:
        await message.channel.send(result[0]['content'])