import discord
from googleapiclient.discovery import build
from googleapiclient import errors

searchService = None
searches = [{}]

def init(google_key):
    global searchService
    try:
        searchService = build('customsearch', 'v1', developerKey=google_key)
    except errors.HttpError:  # sometimes this happens for some reason
        print("Daily quota exceeded!")


async def search(message):
    try:
        query = message.clean_content.split(' ', 1)[1]  # splits the img and the rest of the command
        res = searchService.cse().list(q=query,
                                       cx="017178301722928584583:yi4kptiqtbq",
                                       searchType="image").execute()
        embed = discord.Embed()
        embed.title = "Image Search for " + query
        embed.set_image(url=res['items'][0]['link']).set_footer(text="Page 1 of " + str(len(res['items']))) \
            .set_author(name=message.author.display_name, icon_url=message.author.avatar_url)

        sent = await message.channel.send(embed=embed)  # save the message
        meta = {'chan': message.channel.id, 'msg': sent, 'res': res, 'pg': 1,
                'author': message.author.id}  # store the message channel, the message to edit, the query results, the page we're on, and the author
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


async def stop(message):
    if not searches[0]:
        return
    for item in searches:
        if item['chan'] == message.channel.id and item['pg']:
            if item['author'] != message.author.id:
                break
            await item['msg'].delete()
            await message.delete()
            break


async def advance(message):
    if not searches[0]:
        return
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
            await edit_embed(item, embed, message)
            break


async def jump(message):
    if not searches[0]:
        return
    try:
        page = int(message.clean_content[1:])
    except ValueError:
        return
    for item in searches:
        if item['chan'] == message.channel.id and item['pg']:
            if item['author'] != message.author.id:
                break
            embed = item['msg'].embeds[0]
            item['pg'] = page
            await edit_embed(item, embed, message)
            break


async def edit_embed(results, embed, message):
    embed.set_image(url=results['res']['items'][results['pg'] - 1]['link']) \
        .set_footer(text="Page " + str(results['pg']) + " of " + str(len(results['res']['items'])))  # replace the embed
    await results['msg'].edit(embed=embed)
    await message.delete()
