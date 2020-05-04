import asyncio

import discord

shucks = [
	'https://i.imgur.com/gacRkVx.png',
	'https://i.imgur.com/gacRkVx.png',
	'https://i.imgur.com/gacRkVx.png',
	'https://i.imgur.com/MJRUgWk.png',
	'https://i.imgur.com/UOdRaHR.png',
	'https://i.imgur.com/31jOGPf.png',
	'https://i.imgur.com/k7kTT2o.png',
	'https://i.imgur.com/JvbBhc2.png',
	'https://i.imgur.com/gWfuFB8.png',
	'https://i.imgur.com/Dfz2xpo.png',
	'https://i.imgur.com/EByj26t.png',
	'https://i.imgur.com/tZxutE8.png',
	'https://i.imgur.com/vkSksOv.png',
	'https://i.imgur.com/G5KGuus.png',
	'https://i.imgur.com/MtGmg3w.png',
	'https://i.imgur.com/wnSibNm.png',
	'https://i.imgur.com/cRDaS4i.png',
	'https://i.imgur.com/mh1gqPV.png',
	'https://i.imgur.com/0NgYWV7.png',
	'https://i.imgur.com/CaIMs7Y.png',
	'https://i.imgur.com/TQrwHx6.png',
	'https://i.imgur.com/AX4Fsqr.png',
	'https://i.imgur.com/inKNjPt.png'
]

commands = [
    # {'command': 'prefix <character>', 'info': "Changes the command prefix for the server"},
    {'command': 'i/im/img <query>', 'info': "Google image searches for an image", 'page': 1},
    {'command': 't/tag <tag> | t/tag add/edit <tag> <content> | t/tag owner/remove <tag>',
     'info': 'Access, add, edit, and remove a tag, or find its owner', 'page': 1},
    {'command': 'metar <ICAO airport code>', 'info': 'Meteorological aviation data', 'page': 1},
    {'command': 'ping', 'info': 'Measures Shuckbot\'s ping', 'page': 1},
    {'command': 'hold/holding <image URL / @user>', 'info': 'A perplexed man will hold your image', 'page': 2},
    {'command': 'exm/exmilitary <image URL / @user>', 'info': 'Your image will turn into Sacramento based experimental hip hop band Death Grip\'s first mixtape', 'page': 2},
    {'command': 'fan/fantano/review/tnd <image URL / @user>', 'info': 'Funny internet music man will review your image', 'page': 2},
    {'command': 'kim <image URL / @user>', 'info': 'Your image will be applauded by the Supreme Leader of North Korea and his team', 'page': 2},
    {'command': '1/1bit/one <image URL / @user>', 'info': 'Your image will be represented in 1-bit colour space', 'page': 3},
    {'command': 'e <emote> <scale (optional)>', 'info': 'Your emote will become an image', 'page': 1},
	{'command': 'sort/pixelsort <image URL / @user>', 'info': 'Your image\'s pixels will be sorted from darkest to lightest', 'page': 3},
	{'command': 'Page 1: ', 'info': 'General Commands', 'page': 0},
	{'command': 'Page 2: ', 'info': 'Image editor Commands', 'page': 0},
	{'command': 'Page 3: ', 'info': 'Image filter Commands', 'page': 0},
	{'command': 'Access other pages with', 'info': ';help <page #>', 'page': 0}
]


async def show_help(message, client, ownerID):
	bill = client.get_user(ownerID)
	# shuck = client.get_user(701021789664575498)
	if(len(message.content) == 5):
		page_num = 0
	else:
		page_num = int(message.content[6:])
		if page_num > 3:
			page_num = 3

	embed = discord.Embed()

	titles = ["Shuckbot help", "General commands", "Image editor commands", "Image filter commands"]

	embed.title = titles[page_num]
	embed.type = "rich"
	embed.colour = discord.Color.gold()
	for item in commands:
		if item['page'] == page_num:
			embed.add_field(name=item['command'], value=item['info'], inline=False)
	embed.set_footer(text="Page "+str(page_num)+"/3     type ;help <page number> to see the other pages!",
					 icon_url=shucks[message.id % 23])
	msg = await message.channel.send(embed=embed)
	# reactL = await msg.add_reaction(":shuckL:706690260519747604")
	# reactR = await msg.add_reaction(":shuckR:706690259890733087")
	#
	# def check(reaction, user):
	# 	return user == message.author and (reaction.emoji == reactL or reaction.emoji == reactR)
	#
	# try:
	# 	reaction, user = await client.wait_for('reaction_add', timeout=10.0, check=check)
	# except asyncio.TimeoutError:
	# 	await message.channel.send('TIMEOUT')
	# else:
	# 	await message.channel.send('yes')
