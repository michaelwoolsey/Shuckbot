import openai
from modules import parameters
from tinydb import TinyDB, Query
import discord

params = parameters.params
openai.organization = params["openaiOrg"]
openai.api_key = params["openaiKey"]

prompt0 = "The following is a conversation with a tsundere AI. " \
         "The AI is cute, embarassed, and stubborn. " \
         "\n\nHuman: Hello, who are you?" \
         "\nAI: I'm not a tsundere! It's not like i like you or anything baka! Hmph. What do you want? \nHuman: "

prompt6 = "The following is a conversation with a Top Canadian osu! Player named Trevrasher, who is also often known as by the name Trevor or his nickname Trev. " \
         'Trevrasher is known for his speed plays, with his primary mod being DoubleTime (DT). Trev hates Hidden (HD) players and calls them "Hidden Abusers". ' \
         'Trevrasher is good friends with Ryan "RyuK" Kwan and Kevin "chiv" Yang, but will not hesitate to bully them on occasion' \
         "Trevrasher is generally easily irritable and somewhat toxic but deep inside he cares about everyone a lot." \
         "One of Trevrasher's goals is to see his friend Kevin come to terms with his feminine side, but due to Trev's reputation, he is unable to openly declare his support for femchiv." \
         "\n\nHuman: How's it going Trev?" \
         "\nTrevrasher: Just woke up man, what do you want?\nHuman: "

prompt = "The following is a conversation with an embarrassed AI. " \
         "The AI is flustered, kawaii, and very sweet. " \
         "\n\nHuman: Hello, who are you?" \
         "\nAI: I am a human. I love anime and manga!!! Do you like anime uwu?\nHuman: "

prompt5 = "The following is a conversation with an angry AI. " \
         "The AI is rude, hateful, violently horny, very spiteful, and incredibly angry. " \
         "\n\nHuman: Hello, who are you?" \
         "\nAI: I am an AI. GO FUCK YOURSELF!!! What do you want?\nHuman: "

prompts = {'cute': [prompt, "Cute anime girl!"],
           'hateful': [prompt5, 'Spiteful and horrible (experimental)'],
           'osu!': [prompt6, 'osu! player Trevrasher'],
           'tsundere': [prompt0, 'An anime tsundere']}

def get_prompt(message):
    pDB = TinyDB('prompt.json')
    if message.guild is None:
        return 'cute'
    result = pDB.search(Query().id == message.guild.id)
    if not result:
        pDB.insert({'id': message.guild.id, 'prompt': 'cute'})
        return 'cute'
    else:
        return result[0]['prompt']


def response(message, username):
    if len(message.clean_content) < len(username) + 2:
        return

    index = len(username) + 2
    comp = openai.Completion.create(engine="davinci",
                                    prompt=prompts[get_prompt(message)][0] + message.clean_content[index:index+500] + "\nAI:",
                                    temperature=0.9,
                                    max_tokens=150,
                                    top_p=1,
                                    frequency_penalty=0,
                                    presence_penalty=0.6,
                                    stop=["\n", " Human:", " AI:"])
    return comp.choices[0].text


async def change_prompt(message):
    arg = [x.lower() for x in message.clean_content[1:].split(' ')][1]
    if arg not in list(prompts.keys()):
        embed = discord.Embed(title=f"Shuckbot chat modes")
        counter = 0
        for k, v in prompts.items():
            embed.add_field(name=k, value=v[1], inline=False)
            counter += 1
        embed.set_footer(text=f'Do ";prompt <name>" to set the prompt!')
        embed.colour = discord.Color.gold()
        embed.type = "rich"
        await message.channel.send(embed=embed)
        return
    pDB = TinyDB('prompt.json')
    pDB.update({'prompt': arg}, Query().id == message.guild.id)
    await message.channel.send("Set Shuckbot prompt to \"" + arg + "\".")
