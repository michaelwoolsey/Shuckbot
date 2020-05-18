import discord

async def shucklist(message, client):
    global messages
    shucks = []
    for x in client.emojis:
        if 'shuck' in x.name:
            shucks.append(x)

    messages = ['']
    for x in shucks:
        # Split up shucklist into multiple messages for discord 2000 char limit
        if (len(messages[-1]) + len(str(x))) > 2000:
            messages.append(str(x))
        else:
            messages[-1] = messages[-1] + str(x)

    await message.channel.send('All shucks on this server:')
    for to_send in messages:
        await message.channel.send(to_send)
