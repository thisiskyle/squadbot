# squadbot.py

# TODO/bug: maybe before we close a quorum, we should audit the votes and make sure there isnt a double vote?
#           if squadbot is turned off and someone votes for yes and no, we can just remove those votes?

import os
import discord
import config
import json

#class Quorum_Data:
#    ids = []
#    authors = []
#    contents = []
#    ayes = []
#    nays = []


emoji_thumbsup = '\N{THUMBS UP SIGN}'
emoji_thumbsdown = '\N{THUMBS DOWN SIGN}'
result_unresolved = "unresolved"
result_pass = "pass"
result_fail = "fail"
result_tie = "tie"
status_open = "open"
status_closed = "closed"


# setup client intents
custom_intents = discord.Intents.default()
custom_intents.members = True
custom_intents.guilds = True


# edits the message with the results of the quorum
async def post_results(message, result_string):
    print(f"\nQuorum {message.id}, {result_string}")
    new_content = message.content.replace(status_open, status_closed).replace(result_unresolved, result_string)
    await message.edit(content=new_content)


# get the total members of a guild, excluding bots
def get_member_count(guild):
    return len([m for m in guild.members if not m.bot])


# returns the number of members in guild with a matching role name
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

    if not payload.member.bot and payload.channel_id == config.quorum_channel_id:
        channel = client.get_channel(config.quorum_channel_id)
        message = await channel.fetch_message(payload.message_id)

        proposal = json.loads(message.content)

        # if the quorum is closed
        if proposal['status'] == status_closed:
            print("This quorum is closed, vote ignored")
            return
    else:
        return

    member_count = get_member_count(message.guild)

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
    if nays != None and ayes != None and ayes.count + nays.count == member_count + 2:
        await close_quorum(message, ayes.count, nays.count)


# decide outcome of a quorum
async def close_quorum(message, ayes, nays):

    print(f"\nClosing quorum {message.id}")

    if ayes > nays:
        await post_results(message, result_pass)
    elif nays > ayes:
        await post_results(message, result_fail)
    else:
        await post_results(message, result_unresolved)

#
# closes the quorum in its current state
# missing votes default to "aye"
#
async def force_close_quorum(message):
    member_count = get_member_count(message.guild)
    nays = None 
    ayes = None

    # collect the reactions
    for r in message.reactions:
        # collect votes
        if r.emoji == emoji_thumbsup:
            ayes = r
        elif r.emoji == emoji_thumbsdown:
            nays = r

    # unused votes are automatically counted as "aye"
    extra_ayes = member_count - (ayes.count + nays.count)
    await close_quorum(message, ayes.count + extra_ayes, nays.count)


# handles the close command
async def handle_command_close(message):

    # split the content of the command
    command = message.content.split(" ", 1)

    channel = client.get_channel(config.quorum_channel_id)
    m = await channel.fetch_message(int(command[1]))
    await force_close_quorum(m)



# handles the !quorum command
async def handle_command_quorum(message):

    # get quorum channel
    channel = client.get_channel(config.quorum_channel_id)
    # split the content of the command
    command = message.content.split(" ", 1)
    # create temp message to get message ID
    response = await channel.send("---")

    proposal = {
        "id": response.id,
        "author_id": message.author.id,
        "author_name": message.author.name,
        "status": status_open,
        "result": result_unresolved,
        "proposal": command[1]
    }

    await response.edit(content=json.dumps(proposal, indent=4))
    await response.add_reaction(emoji_thumbsup)
    await response.add_reaction(emoji_thumbsdown)

    # TODO/feature: create a link to the quorum in the original channel


# handles the !help command
async def handle_command_help(message):
    print("someone needs !help. we should finish this command...")


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

    # split the content of the command
    command = message.content.split(" ", 1)

    # if we didnt get a body with the command, ignore it and return
    if len(command) < 2:
        return

    if command[0] == "!quorum" or command[0] == "!q":
        await handle_command_quorum(message)

    elif command[0] == "!close":
        await handle_command_close(message)

    elif command[0] == "!help":
        await handle_command_help()


# when someone adds a vote
@client.event
async def on_raw_reaction_add(payload):
    await handle_vote(payload)


# start the bot
client.run(config.token)
