# squadbot.py

# TODO/bug: maybe before we close a quorum, we should audit the votes and make sure there isnt a double vote?
#           if squadbot is turned off and someone votes for yes and no, we can just remove those votes?

import os
import discord
import config
import json


quorum_ids = []
quorum_authors = []
quorum_contents = []
quorum_ayes = []
quorum_nays = []
quorum_status = []
quorum_results = []


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
custom_intents.message_content = True


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

    print(f"\nVote Received")

    if str(payload.emoji) != str(emoji_thumbsdown) and str(payload.emoji) != str(emoji_thumbsup):
        print(f"Reacting with {payload.emoji} is an invalid vote. Vote ignored")
        return

    if payload.member.bot:
        print("Bot vote ignored")
        return

    if payload.channel_id != config.quorum_channel_id:
        print("Reaction not in quorum channel, vote ignored")
        return

    channel = client.get_channel(config.quorum_channel_id)
    message = await channel.fetch_message(payload.message_id)
    proposal = json.loads(message.content)

    if proposal['status'] == status_closed:
        print("This quorum is closed, vote ignored")
        return

    print(f"\n{payload.member.name} voted {payload.emoji}" )

    nays = None 
    ayes = None

    # collect the reactions
    for r in message.reactions:
        # if its not thumbsup or thumbs down, skip it
        if r.emoji != emoji_thumbsup and r.emoji != emoji_thumbsdown:
            continue

        users = [user async for user in r.users()]
        if payload.member in users and str(r.emoji) != str(payload.emoji):
            print(f"\n{payload.member.name} is changing vote, removing previous reaction")
            await message.remove_reaction(r.emoji, payload.member)

        # count votes
        if r.emoji == emoji_thumbsup:
            ayes = r
        elif r.emoji == emoji_thumbsdown:
            nays = r


    member_count = get_member_count(message.guild)
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


# closes the quorum in its current state missing votes default to "aye"
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

    # if we didnt get a body with the command, ignore it and return
    if len(command) < 2:
        return

    channel = client.get_channel(config.quorum_channel_id)
    m = await channel.fetch_message(int(command[1]))
    await force_close_quorum(m)



# handles the !quorum command
async def handle_command_quorum(message):

    # split the content of the command
    command = message.content.split(" ", 1)

    # if we didnt get a body with the command, ignore it and return
    if len(command) < 2:
        return

    # get quorum channel
    channel = client.get_channel(config.quorum_channel_id)

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

    await message.channel.send(f"A new quorum has been called!\n\nThis isn't like the electoral college, your vote actually matters!\nSo get out there and vote!\n\nFollow this link: {response.jump_url}")

#
def save_to_file():
    print("Saving quorum data to file")
    qobj = {
        "ids": quorum_ids,
        "author_ids": quorum_authors,
        "status": quorum_status,
        "results": quorum_results,
        "proposals": quorum_contents,
        "ayes": quorum_ayes,
        "nays": quorum_nays
    }

    with open("quorums.json", "w") as outfile:
        outfile.write(json.dumps(qobj, indent=4))


#
def load_from_file():
    print("Loading quorum data from file")

    f = open("quorums.json", "w")

    qobj = json.load(f)

    quorum_ids = qobj['ids']
    quorum_authors = qobj['author_ids']
    quorum_contents = qobj['proposals']
    quorum_ayes = qobj['ayes']
    quorum_nays = qobj['nays']
    quorum_status = qobj['status']
    quorum_results = qobj['results']


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
    print("Incoming message...")

    if message.author.bot:
        print("Author is a bot, ignoring")
        return

    # split the content of the command
    command = message.content.split(" ", 1)

    if command[0] == "!quorum" or command[0] == "!q":
        print("!quorum command found")
        await handle_command_quorum(message)

    elif command[0] == "!close":
        print("!close command found")
        await handle_command_close(message)

    elif command[0] == "!help":
        print("!help command found")
        await handle_command_help()


# when someone adds a vote
@client.event
async def on_raw_reaction_add(payload):
    await handle_vote(payload)


# start the bot
client.run(config.token)
