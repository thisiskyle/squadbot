# squadbot.py
# TODO/feature: add a timeout date
# TODO/feature: add a text file that stores the quorum message IDs
# TODO/feature: add more logging

import os
import discord
from config import token, quorum_channel_id, test_channel_id, guild_id


emoji_thumbsup = '\N{THUMBS UP SIGN}'
emoji_thumbsdown = '\N{THUMBS DOWN SIGN}'
result_pass = "pass"
result_fail = "fail"
result_tie = "tie"
status_open = "open"
status_closed = "closed"

# setup client intents
custom_intents = discord.Intents.default()
custom_intents.members = True
custom_intents.guilds = True


#
# get the token
#
def get_token():
    # open the file containing our token
    file = open("token.txt", "r")
    # read the first line
    t = file.readline()
    # close file
    file.close()
    # return the token
    return t


#
# edits the message with the results of the quorum
#
async def post_results(message, result_string):
        print(f"\nQuorum {message.id}, {result_string}")
        new_content = message.content.replace(status_open, status_closed + "\n__**Result:**__ " + result_string)
        await message.edit(content=new_content)



#
# returns the number of members in guild
# with a matching role name
#
def get_role_count(guild, role_name):
    count = 0
    for member in guild.members:
        for role in member.roles:
            if role.name == role_name:
                count += 1
    return count


# handle when someone just voted
async def handle_vote(payload):

    print(f"\nVote Received:\n{payload}")

    #if not payload.member.bot and payload.channel_id == quorum_channel_id:
    if not payload.member.bot and payload.channel_id == test_channel_id:
        #channel = client.get_channel(quorum_channel_id)
        channel = client.get_channel(test_channel_id)
        message = await channel.fetch_message(payload.message_id)

        # if the quorum is closed
        if status_closed in message.content:
            print("This quorum is closed, vote ignored")
            return
    else:
        return

    camper_count = get_role_count(client.get_guild(guild_id), "camper-2022")

    nays = None 
    ayes = None

    # collect the reactions
    for r in message.reactions:
        # checks the reactant isn't a bot and the emoji isn't the one they just reacted with
        if payload.member in await r.users().flatten() and not payload.member.bot and str(r) != str(payload.emoji):
            print(f"\n{payload.member.name} is changing vote")
            await message.remove_reaction(r.emoji, payload.member)

        # collect votes
        if r.emoji == emoji_thumbsup:
            ayes = r
        elif r.emoji == emoji_thumbsdown:
            nays = r

    # post results if closed
    if nays != None and ayes != None and ayes.count + nays.count == camper_count + 2:
        await close_quorum(message, ayes.count, nays.count)


#
# decide outcome of a quorum
#
async def close_quorum(message, ayes, nays):

        print(f"\nClosing quorum {message.id}")

        if ayes > nays:
            await post_results(message, result_pass)
        elif nays > ayes:
            await post_results(message, result_fail)
        elif nays == ayes:
            await post_results(message, result_tie)

#
# closes the quorum in its current state
# missing votes default to "aye"
#
async def force_close_quorum(message):
    camper_count = get_role_count(client.get_guild(guild_id), "camper-2022") + 2
    nays = None 
    ayes = None

    # collect the reactions
    for r in message.reactions:
        # collect votes
        if r.emoji == emoji_thumbsup:
            ayes = r
        elif r.emoji == emoji_thumbsdown:
            nays = r

    extra_ayes = camper_count - (ayes.count + nays.count)
    await close_quorum(message, ayes.count + extra_ayes, nays.count)

#
# handles the close command
#
async def handle_close(message):
        # split the content of the command
        command = message.content.split(" ", 1)

        # if we didnt get a body with the command, ignore it and return
        if len(command) < 2:
            return

        channel = client.get_channel(test_channel_id)
        m = await channel.fetch_message(int(command[1]))
        await force_close_quorum(m)


#
# handles the quorum command
#
async def handle_quorum(message):

        # split the content of the command
        command = message.content.split(" ", 1)

        # if we didnt get a body with the command, ignore it and return
        if len(command) < 2:
            return

        # get quorum channel
        #channel = client.get_channel(quorum_channel_id)
        channel = client.get_channel(test_channel_id)

        # get @campers-2022 role
        role = discord.utils.get(message.guild.roles, name="camper-2022")

        # create temp message to get message ID
        response = await channel.send("---")

        # build the response string
        # this is formatted weird because of the special triple quote
        #prop_string = f"""---- <@&{role.id}>
        prop_string = f"""-
__**Quorum ID:**__ {response.id}
__**Status:**__ {status_open}
__**Caller:**__ {message.author.name}
__**Subject:**__ {command[1]}
"""

        await response.edit(content=prop_string)
        await response.add_reaction(emoji_thumbsup)
        await response.add_reaction(emoji_thumbsdown)


# start client
client = discord.Client(intents=custom_intents)

#
# when the bot logs on
#
@client.event
async def on_ready():
    print(f'{client.user} connected!')

#
# this functions listens for a message
#
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if "!quorum" in message.content:
        await handle_quorum(message)

    if "!close" in message.content:
        await handle_close(message)

#
# when someone adds a vote
#
@client.event
async def on_raw_reaction_add(payload):
    await handle_vote(payload)


# start the bot
client.run(token)
