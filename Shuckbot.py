import logging
import sys
import traceback
from datetime import datetime
from tinydb import TinyDB, Query

import discord
from discord.ext import commands

from modules import tags, imagesearch, metar, imagefun, help, picturebook, cleverbot, games, parameters, openai

params = parameters.params

imagesearch.init(params["googleKey"])
logging.basicConfig(level=logging.INFO)

defaultPrefix = ';'

prefixDB = TinyDB('prefixes.json')


def process_prefix(p_bot, message):
    if message.guild is None:
        return ';'
    result = prefixDB.search(Query().id == message.guild.id)
    if not result:
        prefixDB.insert({'id': message.guild.id, 'prefix': ';'})
        return ';'
    else:
        return result[0]['prefix']


bot = commands.Bot(command_prefix=process_prefix, intents=discord.Intents.default())
bot.remove_command("help")  # discord.py ships with a default help command: must remove it

@bot.command()
async def engines(ctx):
    openai.engine_list()

@bot.command(aliases=["shuckbotprefix", "shuckprefix"])
async def prefix(ctx, *args):
    if not ctx.message.author.guild_permissions.manage_guild or not ctx.message.author.guild_permissions.administrator:
        await ctx.channel.send("You need the **Manage Server** permission to do that.")
    elif len(args) > 1 or len(args) == 0 or len(args[0]) > 1:
        await ctx.channel.send("**Format**: ;prefix <single character>")
    elif not args[0].isascii():
        await ctx.channel.send("You must choose an ASCII character!")
    else:
        prefixDB.update({'prefix': args[0]}, Query().id == ctx.message.guild.id)
        await ctx.channel.send("Set server prefix to \"" + args[0] + "\".")


@bot.command()
async def ping(ctx):
    now = datetime.now()
    sent = await ctx.channel.send("Measuring ping...")
    diff = sent.created_at - now
    await sent.edit(content="Pong! Shuckbot's ping is **" + str(int(diff.microseconds / 1000)) + "**ms.")


@bot.command(aliases=["help"])
async def page(ctx):
    await help.show_help(ctx.message)


@bot.command(aliases=["i", "im", "image"])
async def img(ctx):
    await imagesearch.google_search(ctx.message)


@bot.command()
async def r34(ctx):
    await imagesearch.r34_search(ctx.message)


@bot.command()
async def invite(ctx):
    await ctx.channel.send(
        params["url"])


@bot.command(aliases=["picturebook", "photobook"])
async def pb(ctx, *args):
    if ' ' not in ctx.message:
        await picturebook.get_saved(ctx.message)

    else:
        _arg = args[0]  # the first argument

        if _arg == 'add' or _arg == 'save':
            await picturebook.save(ctx.message)

        elif _arg == 'remove' or _arg == "delete" or _arg == "rm":
            await picturebook.remove(ctx.message, params["ownerID"])


@bot.command(aliases=["t"])
async def tag(ctx, *args):
    if len(args) == 0:
        await tags.syntax_error(ctx.message)
    else:
        if args[0] == 'add':
            await tags.add(ctx.message)

        elif args[0] == 'remove' or args[0] == "delete":
            await tags.remove(ctx.message, params["ownerID"])

        elif args[0] == 'edit':
            await tags.edit(ctx.message, params["ownerID"])

        elif args[0] == 'owner':
            owner_id = tags.owner(ctx.message)
            tag_owner = await bot.fetch_user(owner_id)
            if tag_owner == 0:
                await ctx.channel.send("Tag **" + args[1] + "** does not exist")
            else:
                await ctx.channel.send("Tag **" + args[1] + "** is owned by `" + str(tag_owner) + "`")

        elif args[0] == 'list':
            await tags.owned(ctx.message)

        elif args[0] == 'random':
            await tags.get_random(ctx.message)

        else:
            await tags.get(ctx.message)


@bot.command()
async def metar(ctx):
    await metar.metar(ctx.message, params["avwxKey"])


@bot.command(aliases=["hold"])
async def holding(ctx):
    await imagefun.holding_imagemaker(ctx.message)


@bot.command(aliases=["exmilitary"])
async def exm(ctx):
    await imagefun.exmilitary_imagemaker(ctx.message)


@bot.command(aliases=["fan", "review", "tnd"])
async def fantano(ctx):
    await imagefun.fantano_imagemaker(ctx.message)


@bot.command(aliases=["1bit", "1"])
async def one(ctx):
    await imagefun.one_imagemaker(ctx.message)


@bot.command()
async def kim(ctx):
    await imagefun.kim_imagemaker(ctx.message)


@bot.command(aliases=["e"])
async def emote(ctx):
    await imagefun.get_emoji(ctx.message, bot)


@bot.command(aliases=["pixelsort", "sortpixels"])
async def sort(ctx):
    await imagefun.sort_pixels(ctx.message)


@bot.command(aliases=["pixelshuffle"])
async def shuffle(ctx):
    await imagefun.pixel_shuffle(ctx.message)


@bot.command(aliases=["scale"])
async def resize(ctx):
    await imagefun.resize_img(ctx.message)


@bot.command()
async def size(ctx):
    await imagefun.get_size(ctx.message)


@bot.command(aliases=["mina"])
async def twice(ctx):
    await imagefun.twice_imagemaker(ctx.message)


@bot.command(aliases=["drawing"])
async def draw(ctx):
    await imagefun.drawing_imagemaker(ctx.message)


@bot.command()
async def undo(ctx):
    await imagefun.undo_img(ctx.message)


@bot.command(aliases=["loona"])
async def heejin(ctx):
    await imagefun.heejin_imagemaker(ctx.message)


@bot.command()
async def school(ctx):
    await imagefun.school_imagemaker(ctx.message)


@bot.command(aliases=["lect"])
async def lecture(ctx):
    await imagefun.lecture_imagemaker(ctx.message)


@bot.command()
async def tesla(ctx):
    await imagefun.tesla_imagemaker(ctx.message)


@bot.command()
async def osu(ctx):
    await imagefun.osu_imagemaker(ctx.message)


@bot.command(aliases=["colour", "c"])
async def color(ctx):
    await imagefun.get_colour_from_hex(ctx.message)


@bot.command(aliases=["noisy"])
async def mix(ctx):
    await imagefun.mixer(ctx.message)


@bot.command()
async def noise(ctx):
    await imagefun.noise_imagemaker(ctx.message)


@bot.command(aliases=["gf"])
async def mokou(ctx):
    await imagefun.mokou_imagemaker(ctx.message)


@bot.command()
async def shift(ctx):
    await imagefun.image_shift(ctx.message)


@bot.command(aliases=["megu"])
async def megumin(ctx):
    await imagefun.megumin_imagemaker(ctx.message)


@bot.command()
async def weezer(ctx):
    await imagefun.weezer_imagemaker(ctx.message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send('Sorry, this command is on cooldown! Try again in {:.2f} seconds'.format(error.retry_after))


@commands.cooldown(1, 5, commands.BucketType.guild)
@bot.command(aliases=["g"])
async def game(ctx):
    try:
        await games.game(ctx.message, bot, params["mapquest"])
    except Exception as e:
        await ctx.send(f'An error has occured! Go yell at @michaeL#9999 to fix it. You should also give him this:')
        await ctx.send(f'```{traceback.format_exc()}```')


@bot.command(aliases=["torgb", "2rgb"])
async def rgb(ctx):
    await imagefun.to_rgb(ctx.message)


@bot.command(aliases=["a"])
async def avatar(ctx):
    await imagefun.get_avatar(ctx.message)


@bot.command()
async def purple(ctx):
    await imagefun.purple(ctx.message)


@bot.command()
async def whatifitwaspurple(ctx):
    await imagefun.whatifitwaspurple(ctx.message)


@bot.command(aliases=["tom"])
async def tomscott(ctx):
    await imagefun.tom_imagemaker(ctx.message)


@bot.command()
async def sickos(ctx):
    await imagefun.sickos_imagemaker(ctx.message)


@bot.command(aliases=['prompt', 'setprompt', 'mode'])
async def changeprompt(ctx):
    await openai.change_prompt(ctx.message)


@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.clean_content.lower() == "b" or message.clean_content.lower() == "n":
        await imagesearch.advance(message)

    elif message.clean_content.lower().startswith("p"):
        await imagesearch.jump(message)

    elif message.clean_content.lower() == "s":
        await imagesearch.stop(message)

    elif message.clean_content.startswith("@" + message.guild.get_member(bot.user.id).display_name):
        await message.channel.trigger_typing()
        try:
            await message.channel.send(
                # cleverbot.cleverbot_message(message, message.guild.get_member(bot.user.id).display_name))
                openai.response(message, message.guild.get_member(bot.user.id).display_name))
        except discord.HTTPException:
            await message.channel.send("guh")

bot.run(params["token"])
