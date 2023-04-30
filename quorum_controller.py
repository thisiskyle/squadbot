
# TODO/bug: maybe before we close a quorum, we should audit the votes and make sure there isnt a double vote?
#           if squadbot is turned off and someone votes for yes and no, we can just remove those votes?

import emoji as em
import discord
import discord_helpers as dh
import config
import time

result_unresolved = "None"
result_pass = "Pass"
result_fail = "Fail"
result_tie = "Tie"
status_open = "Open"
status_closed = "Closed"


field_index_id = 0
field_index_author = 1
field_index_status = 2
field_index_result = 3
field_index_proposal = 4
field_index_ayes = 5
field_index_nays = 6


# edits the message with the results of the quorum
async def post_results(message, result_string, ayes, nays):
    print(f"\nQuorum {message.id}, {result_string}")

    embd = message.embeds[0]
    status_field = embd.fields[field_index_status]
    result_field = embd.fields[field_index_result]

    embd.set_field_at(field_index_status, name="Status", value=status_closed, inline=False)
    embd.set_field_at(field_index_result, name="Result", value=result_string, inline=False)
    embd.set_field_at(field_index_ayes, name="Ayes", value=str(ayes), inline=True)
    embd.set_field_at(field_index_nays, name="Nays", value=str(nays), inline=True)

    await message.edit(content=None, embed=embd)

#
async def handle_vote(bot, ctx):

    print(f"\nVote Received")

    if str(ctx.emoji) != str(em.thumbsdown) and str(ctx.emoji) != str(em.thumbsup):
        print(f"Reacting with {ctx.emoji} is an invalid vote. Vote ignored")
        return

    if ctx.member.bot:
        print("Bot vote ignored")
        return

    if ctx.channel_id != config.quorum_channel_id:
        print("Reaction not in quorum channel, vote ignored")
        return

    channel = bot.get_channel(config.quorum_channel_id)
    message = await channel.fetch_message(ctx.message_id)
    message_embed = message.embeds[0]

    if message_embed.fields[field_index_status].value == status_closed:
        print("This quorum is closed, vote ignored")
        return

    print(f"\n{ctx.member.name} voted {ctx.emoji}" )

    # collect the reactions
    for r in message.reactions:
        # if its not thumbsup or thumbs down, skip it
        if r.emoji != em.thumbsup and r.emoji != em.thumbsdown:
            continue

        users = [user async for user in r.users()]
        if ctx.member in users and str(r.emoji) != str(ctx.emoji):
            print(f"\n{ctx.member.name} is changing vote, removing previous reaction")
            await message.remove_reaction(r.emoji, ctx.member)


    # TODO/bug: this section is supposed to update the embed, but it doesnt work
    nays = None 
    ayes = None
    for r in message.reactions:
        # count votes
        if r.emoji == em.thumbsup:
            ayes = r.count - 1
        elif r.emoji == em.thumbsdown:
            nays = r.count - 1

    message_embed.set_field_at(field_index_ayes, name="Ayes", value=str(ayes), inline=True)
    message_embed.set_field_at(field_index_nays, name="Nays", value=str(nays), inline=True)
    await message.edit(content=None, embed=message_embed)


    member_count = dh.get_member_count(message.guild)
    # post results if closed
    if nays != None and ayes != None and ayes + nays == member_count:
        await close_quorum(message, ayes, nays)



async def refresh_votes(bot, message):

    # split the content of the command
    command = message.content.split(" ", 1)

    # if we didnt get a body with the command, ignore it and return
    if len(command) < 2:
        return

    channel = bot.get_channel(config.quorum_channel_id)
    m = await channel.fetch_message(int(command[1]))

    nays = None 
    ayes = None

    message_embed = m.embeds[0]

    for r in m.reactions:
        # count votes
        if r.emoji == em.thumbsup:
            ayes = r.count - 1
        elif r.emoji == em.thumbsdown:
            nays = r.count - 1

    message_embed.set_field_at(field_index_ayes, name="Ayes", value=str(ayes), inline=True)
    message_embed.set_field_at(field_index_nays, name="Nays", value=str(nays), inline=True)
    await m.edit(content=None, embed=message_embed)


# decide outcome of a quorum
async def close_quorum(message, ayes, nays):

    print(f"\nClosing quorum {message.id}")

    if ayes > nays:
        await post_results(message, result_pass, ayes, nays)
    elif nays > ayes:
        await post_results(message, result_fail, ayes, nays)
    else:
        await post_results(message, result_unresolved, ayes, nays)


# closes the quorum in its current state missing votes default to "aye"
async def force_close_quorum(message):
    member_count = dh.get_member_count(message.guild)
    nays = None 
    ayes = None

    # collect the reactions
    for r in message.reactions:
        # collect votes
        if r.emoji == em.thumbsup:
            ayes = r
        elif r.emoji == em.thumbsdown:
            nays = r

    # unused votes are automatically counted as "aye"
    extra_ayes = member_count - (ayes.count + nays.count - 2)
    await close_quorum(message, ayes.count + extra_ayes - 1, nays.count - 1)


async def handle_command_close(bot, message):

    # split the content of the command
    command = message.content.split(" ", 1)

    # if we didnt get a body with the command, ignore it and return
    if len(command) < 2:
        return

    channel = bot.get_channel(config.quorum_channel_id)
    m = await channel.fetch_message(int(command[1]))
    await force_close_quorum(m)



async def handle_command_quorum(bot, message):

    # split the content of the command
    command = message.content.split(" ", 1)

    # if we didnt get a body with the command, ignore it and return
    if len(command) < 2:
        return

    # get quorum channel
    quorum_channel = bot.get_channel(config.quorum_channel_id)

    # create temp message to get message ID
    quorum_message = await quorum_channel.send("---")

    new_embed = discord.Embed(title=f"Official Quorum")
    new_embed.add_field(name="ID", value=f"{quorum_message.id}", inline=False)
    new_embed.add_field(name="Author", value=f"{message.author.name}", inline=False)
    new_embed.add_field(name="Status", value=f"{status_open}", inline=False)
    new_embed.add_field(name="Result", value=f"{result_unresolved}", inline=False)
    new_embed.add_field(name="Proposal", value=f"{command[1]}", inline=False)
    new_embed.add_field(name="Ayes", value=str(0), inline=True)
    new_embed.add_field(name="Nays", value=str(0), inline=True)

    # TODO: add some buttons here

    await quorum_message.add_reaction(em.thumbsup)
    await quorum_message.add_reaction(em.thumbsdown)
    await quorum_message.edit(content=None, embed=new_embed)

    # TODO: make this an embed
    #await message.channel.send(f"A new quorum has been called!\n\nThis isn't like the electoral college, your vote actually matters!\nSo get out there and vote!\n\nFollow this link: {response.jump_url}")

