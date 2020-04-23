import discord
import requests
from simplejson.scanner import JSONDecodeError


async def metar(message, token):
    args = message.clean_content.split(' ')
    if len(args) < 2:
        await message.channel.send("Syntax error\n```fix\nmetar <station>```")
    else:
        resp = requests.get("https://avwx.rest/api/metar/" + args[1] + "?token=" + token)
        try:
            result = resp.json()
            if "error" in result.keys():
                await message.channel.send("**Error**: " + result['error'] + ".")
            else:
                emoji = ""
                if result['flight_rules'] == "VFR":
                    emoji += ":green_circle:"
                elif result['flight_rules'] == "MVFR":
                    emoji += ":blue_circle:"
                elif result['flight_rules'] == "IFR":
                    emoji += ":red_circle:"
                elif result['flight_rules'] == "LIFR":
                    emoji += "<:pink_circle:702657173980708974>"
                await message.channel.send(emoji + " `" + result['sanitized'] + "`")
        except JSONDecodeError:
            await message.channel.send("**Error**: " + args[1].upper() + " is not a valid ICAO station ident.")
