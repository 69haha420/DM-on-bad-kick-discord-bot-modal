import config as settings
import logging
import discord
from discord.ext import commands, tasks
from datetime import datetime
from discord import app_commands

logtime = datetime.now().strftime('%Y%m%d-%H%M%S')
logging.basicConfig(level=logging.DEBUG, filename=f"logs/{logtime}.log", filemode="w", encoding="utf-8",
                    format="%(asctime)-30s %(levelname)-15s %(name)-20s %(message)s")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=settings.prfx, intents=intents, help_command=None)


# ON READY
@bot.event
async def on_ready():
    print(
        f"{bot.user} (ID: {bot.user.id}) logged in successfully at {datetime.now().strftime('%H:%M:%S')} on {datetime.now().strftime('%d.%m.%Y')}")
    await bot.tree.sync()
    print("commands synced")
    status_task.start()


# presence loop
@tasks.loop(seconds=60.0)
async def status_task():
    totalcount = await read_count()
    activityname = f"Total Executions: {totalcount}"
    print(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')} - {activityname}")
    await bot.change_presence(activity=discord.Game(activityname), status=discord.Status.dnd)


# BAN
class BanReasonModal(discord.ui.Modal, title="Ban"):
    ban_reason = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label="Ban Reason:",
        required=True,
        placeholder="Spam",
        max_length=500
    )
    deletemessagedays = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Delete messages for last X hours:",
        required=False,
        placeholder="Must be number from 0 to 168!",
    )

    async def on_submit(self, interaction: discord.Interaction):
        bannedmember = self.member
        banauthor = self.user
        banreason = self.ban_reason.value
        server = interaction.guild
        totalcount = await read_count()

        deletemessagehours = self.deletemessagedays.value
        try:
            int(deletemessagehours)
            if 0 <= int(deletemessagehours) <= 168:
                deleteseconds = int(deletemessagehours) * 3600
            else:
                deleteseconds = 0
        except ValueError:
            deleteseconds = 0

        if server.icon != None:
            servericon = server.icon.url
        else:
            servericon = None
        dmbanneduser = discord.Embed(title=f"You were banned!",
                                     description=f"{banauthor.mention} banned you from **{server.name}** with reason: {banreason}",
                                     color=0x00ff00)
        dmbanneduser.set_author(name=banauthor.name, icon_url=banauthor.avatar.url)
        dmbanneduser.set_thumbnail(url=servericon)
        dmbanneduser.set_footer(text=f"Powered by zmotan.com (total ececutions: {totalcount + 1})")

        try:
            await bannedmember.send(embed=dmbanneduser)
            await server.ban(user=bannedmember, reason=banreason, delete_message_seconds=deleteseconds)
            await interaction.response.send_message(
                f"{banauthor.mention}, you banned {bannedmember.mention} with reason: {banreason} and DM was sent.",
                ephemeral=True)
            await add_to_count()
        except discord.errors.NotFound or discord.errors.Forbidden:
            return

    async def on_error(self, interaction: discord.Interaction, error):
        bannedmember = self.member
        banauthor = self.user
        banreason = self.ban_reason.value
        server = interaction.guild
        deletemessagehours = self.deletemessagedays.value
        try:
            int(deletemessagehours)
            if 0 <= int(deletemessagehours) <= 168:
                deleteseconds = int(deletemessagehours) * 3600
            else:
                deleteseconds = 0
        except ValueError:
            deleteseconds = 0
        print(error)
        await server.ban(user=bannedmember, reason=banreason, delete_message_seconds=deleteseconds)
        await interaction.response.send_message(
            f"{banauthor.mention}, you banned {bannedmember.mention} with reason: {banreason}, but {bannedmember.mention} has locked DMs so DM was not sent.",
            ephemeral=True)
        await add_to_count()


# KICK
class KickReasonModal(discord.ui.Modal, title="Kick"):
    kick_reason = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label="Kick Reason:",
        required=True,
        placeholder="Spam",
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        kickedmember = self.member
        kickauthor = self.user
        kickreason = self.kick_reason.value
        server = interaction.guild
        totalcount = await read_count()
        if server.icon != None:
            servericon = server.icon.url
        else:
            servericon = None
        dmkickeduser = discord.Embed(title=f"You were kicked!",
                                     description=f"{kickauthor.mention} kicked you from **{server.name}** with reason: {kickreason}",
                                     color=0x00ff00)
        dmkickeduser.set_author(name=kickauthor.name, icon_url=kickauthor.avatar.url)
        dmkickeduser.set_thumbnail(url=servericon)
        dmkickeduser.set_footer(text=f"Powered by zmotan.com (total ececutions: {totalcount + 1})")

        try:
            await kickedmember.send(embed=dmkickeduser)
            await server.kick(user=kickedmember, reason=kickreason)
            await interaction.response.send_message(
                f"{kickauthor.mention}, you kicked {kickedmember.mention} with reason: {kickreason} and DM was sent.",
                ephemeral=True)
            await add_to_count()
        except discord.errors.NotFound or discord.errors.Forbidden:
            return

    async def on_error(self, interaction: discord.Interaction, error):
        kickedmember = self.member
        kickauthor = self.user
        kickreason = self.kick_reason.value
        server = interaction.guild
        print(error)
        await server.kick(user=kickedmember, reason=kickreason)
        await interaction.response.send_message(
            f"{kickauthor.mention}, you kicked {kickedmember.mention} with reason: {kickreason}, but {kickedmember.mention} has locked DMs so DM was not sent.",
            ephemeral=True)
        await add_to_count()


# Ban context menu
@bot.tree.context_menu(name="BAN")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member):
    if member != bot.user:
        brmodal = BanReasonModal()
        brmodal.user = interaction.user
        brmodal.member = member
        await interaction.response.send_modal(brmodal)
    else:
        await interaction.response.send_message(f"I can't kick myself!", ephemeral=True)


# Bick context menu
@bot.tree.context_menu(name="KICK")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):
    if member != bot.user:
        krmodal = KickReasonModal()
        krmodal.user = interaction.user
        krmodal.member = member
        await interaction.response.send_modal(krmodal)
    else:
        await interaction.response.send_message(f"I can't kick myself!", ephemeral=True)


@bot.tree.error
async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        return await interaction.response.send_message(f"You're missing permissions to do that!", ephemeral=True)
    else:
        raise error


async def add_to_count():
    with open("count.txt", 'r') as file:
        count = file.read().strip()
    with open("count.txt", 'w') as file:
        newcount = int(count) + 1
        file.write(f'{newcount}')


async def read_count():
    with open("count.txt", 'r') as file:
        totalcount = file.read().strip()
    return int(totalcount)


bot.run(settings.discord_token)
