# squadbot.py

import os
import discord


# get the token
def get_token():
    # open the file containing our token
    file = open("token.txt", "r")
    # read the first line
    t = file.readline()
    # close file
    file.close()
    # return the token
    return t


# edits the message with the results of the quorum
async def post_results(message, result_string):
        new_content = message.content.replace("Open", "Closed\n**Result:** " + result_string)
        await message.edit(content=new_content)



# returns the number of members in guild
# with a matching role name
def get_role_count(guild, role_name):
    count = 0
    for member in guild.members:
        for role in member.roles:
            if role.name == role_name:
                count += 1
    return count


# handle when someone just voted
async def handle_vote(payload):

    #if payload.channel_id == test_channel_id:
    if payload.channel_id == quorum_channel_id:
        channel = client.get_channel(quorum_channel_id)
        message = await channel.fetch_message(payload.message_id)
        # if the quorum is closed
        if "[closed]" in message.content:
            print("This quorum is closed, vote ignored")
            return
    else:
        return

    camper_count = get_role_count(client.get_guild(guild_id), "camper-2022")

    # we add an extra + 1 to account for the initial
    # add reactions from the bot itself
    count_needed = (int(camper_count / 2)) + 1 + 1

    nays = None
    ayes = None

    # collect the reactions
    for reaction in message.reactions:
        if reaction.emoji == emoji_thumbsup:
            ayes = reaction
        elif reaction.emoji == emoji_thumbsdown:
            nays = reaction

    if nays != None and ayes != None:
        if ayes.count + nays.count == camper_count:
            await post_results(message, "Tied/Rejected")

        elif ayes.count == count_needed:
            await post_results(message, "Accepted")

        elif nays.count == count_needed:
            await post_results(message, "Rejected")
           


# handles the quorum command
async def handle_quorum(message):

        # split the content of the command
        command = message.content.split(" ", 1)

        # if we didnt get a body with the command, ignore it and return
        if len(command) < 2:
            return

        # get quorum channel
        channel = client.get_channel(quorum_channel_id)

        # get @campers-2022 role
        role = discord.utils.get(message.guild.roles, name="camper-2022")

        camper_count = get_role_count(client.get_guild(guild_id), "camper-2022")

        # we add an extra + 1 to account for the initial add reactions from the bot itself
        count_needed = (int(camper_count / 2)) + 1 + 1

        # build the response string
        # this is formatted weird because of the special triple quote
        prop_string = f"""---- <@&{role.id}>
--
__**Proposal \#{len(props) + 1}**__
**Status:** Open
--
**Caller:** {message.author.name}
**Votes Needed:** {count_needed}
**Subject:**

{command[1]}

--
"""
        # save response
        response = await channel.send(prop_string)

        # add the quorum to a list of quorums
        props.append(response)

        # add reactions
        await response.add_reaction(emoji_thumbsup)
        await response.add_reaction(emoji_thumbsdown)



# variables
token = get_token()
quorum_channel_id = 946043443463991316
test_channel_id = 946216621930840064
guild_id = 946041821946085426
props = [ ]
emoji_thumbsup = '\N{THUMBS UP SIGN}'
emoji_thumbsdown = '\N{THUMBS DOWN SIGN}'



# setup client intents
custom_intents = discord.Intents.default()
custom_intents.members = True
custom_intents.guilds = True


# start client
client = discord.Client(intents=custom_intents)



# when the bot logs on
@client.event
async def on_ready():
    print(f'{client.user} connected!')




# this functions listens for a message
@client.event
async def on_message(message):
    if message.author == client.user:
        return


    if "!quorum" in message.content:
        await handle_quorum(message)



# when someone adds a vote
@client.event
async def on_raw_reaction_add(payload):
    await handle_vote(payload)


# start the bot
client.run(token)
