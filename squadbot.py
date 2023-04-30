# squadbot.py

import os
import discord
from discord.ext import commands
import config
import quorum_controller as qc


def run():


    # setup client intents
    custom_intents = discord.Intents.default()
    custom_intents.members = True
    custom_intents.guilds = True
    custom_intents.message_content = True

    #client = discord.Client(intents=custom_intents)
    bot = commands.Bot(command_prefix="!", intents=custom_intents)


    # when the bot logs on
    @bot.event
    async def on_ready():
        print(f'{bot.user} connected!')
        #qc.load_quorum_from_file()

    # when someone adds a vote
    @bot.event
    async def on_raw_reaction_add(ctx):
        await qc.handle_vote(bot, ctx)

    # quorum
    @bot.command()
    async def quorum(ctx):
        await qc.handle_command_quorum(bot, ctx.message)

    # q
    @bot.command()
    async def q(ctx):
        await qc.handle_command_quorum(bot, ctx.message)

    # close quorum
    @bot.command()
    async def close(ctx):
        await qc.handle_command_close(bot, ctx.message)

    @bot.command()
    async def refresh(ctx):
        await qc.refresh_votes(bot, ctx.message)

    # start the bot
    bot.run(config.token)


run()
