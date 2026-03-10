import discord
from discord.ext import commands
from discord import app_commands
import os
import random
import json
from datetime import datetime, timedelta

# -------- Bot Setup --------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # For slash commands

# -------- Data Storage --------
DATA_FILE = "moneh_data.json"

try:
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -------- Helper Functions --------
def get_user(uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            "wallet": 0,
            "bank": 0,
            "cooldowns": {
                "daily": None,
                "work": None,
                "beg": None,
                "crime": None,
                "search": None,
                "rob": None
            },
            "stats": {
                "gambled_times": 0,
                "won": 0,
                "lost": 0
            }
        }
        save_data()
    return data[uid]

def format_cooldown(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0:
        parts.append(f"{secs}s")
    return " ".join(parts) if parts else "Ready ✅"

def check_cooldown(uid, cmd, cd_seconds):
    user = get_user(uid)
    last = user["cooldowns"].get(cmd)
    if last is None:
        return 0
    last_time = datetime.fromisoformat(last)
    remaining = (last_time + timedelta(seconds=cd_seconds) - datetime.utcnow()).total_seconds()
    return max(0, int(remaining))

def set_cooldown(uid, cmd):
    user = get_user(uid)
    user["cooldowns"][cmd] = datetime.utcnow().isoformat()
    save_data()

# -------- Economy Functions --------
async def give_money_embed(interaction, min_amount, max_amount, cmd, cd_seconds, fail_chance=0):
    uid = interaction.user.id
    remaining = check_cooldown(uid, cmd, cd_seconds)
    if remaining > 0:
        embed = discord.Embed(
            title=f"{cmd.capitalize()} Cooldown ⏱",
            description=f"You must wait **{format_cooldown(remaining)}** to use this command again.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if fail_chance and random.randint(1,100) <= fail_chance:
        set_cooldown(uid, cmd)
        embed = discord.Embed(
            title=f"{cmd.capitalize()} Failed ❌",
            description=f"You got nothing this time.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    amount = random.randint(min_amount, max_amount)
    user = get_user(uid)
    user["wallet"] += amount
    set_cooldown(uid, cmd)
    save_data()
    embed = discord.Embed(
        title=f"{cmd.capitalize()} Success 🎉",
        description=f"You earned **{amount} moneh**!\n💰 Wallet: {user['wallet']} moneh\n🏦 Bank: {user['bank']} moneh",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# -------- Slash Commands --------
@tree.command(name="daily", description="Claim your daily moneh (24h)")
async def daily(interaction: discord.Interaction):
    await give_money_embed(interaction, 25000, 50000, "daily", 86400)

@tree.command(name="work", description="Work to earn moneh (every 5 min)")
async def work(interaction: discord.Interaction):
    await give_money_embed(interaction, 500, 5000, "work", 300)

@tree.command(name="beg", description="Beg for moneh (20% chance fail, every 10 min)")
async def beg(interaction: discord.Interaction):
    await give_money_embed(interaction, 750, 7500, "beg", 600, fail_chance=20)

# -------- Crime Command (deduct 2500–5000 on fail, wallet can go negative) --------
@tree.command(name="crime", description="Do a risky crime (10% fail, every 30 min)")
async def crime(interaction: discord.Interaction):
    uid = interaction.user.id
    remaining = check_cooldown(uid, "crime", 1800)
    if remaining > 0:
        embed = discord.Embed(title="⏱ Crime Cooldown", description=f"You must wait {format_cooldown(remaining)} to commit a crime.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    chance = random.randint(1,100)
    user = get_user(uid)
    if chance <= 90:  # success
        amount = random.randint(1500, 30000)
        user["wallet"] += amount
        set_cooldown(uid, "crime")
        save_data()
        embed = discord.Embed(title="💰 Crime Success!", description=f"You successfully committed a crime and earned **{amount} moneh**!\n💰 Wallet: {user['wallet']}", color=discord.Color.green())
    else:  # fail
        lost = random.randint(1000, 5000)
        user["wallet"] -= lost  # wallet can go negative
        set_cooldown(uid, "crime")
        save_data()
        embed = discord.Embed(title="❌ Crime Failed!", description=f"You were caught and fined **{lost} moneh**.\n💰 Wallet may go negative: {user['wallet']}", color=discord.Color.red())
    await interaction.response.send_message(embed=embed)

@tree.command(name="search", description="Search for moneh (every 15 min)")
async def search(interaction: discord.Interaction):
    await give_money_embed(interaction, 1250, 15000, "search", 900)

# -------- Wallet & Bank --------
@tree.command(name="wallet", description="Check your wallet and bank")
async def wallet(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    embed = discord.Embed(
        title=f"{interaction.user.name}'s Wallet & Bank",
        description=f"💰 Wallet: {user['wallet']} moneh\n🏦 Bank: {user['bank']} moneh",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="deposit", description="Deposit moneh into bank")
@app_commands.describe(amount="Amount to deposit")
async def deposit(interaction: discord.Interaction, amount: int):
    user = get_user(interaction.user.id)
    if amount <= 0 or user["wallet"] < amount:
        embed = discord.Embed(title="❌ Deposit Failed", description="Invalid amount or insufficient wallet balance.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    user["wallet"] -= amount
    user["bank"] += amount
    save_data()
    embed = discord.Embed(title="🏦 Deposit Successful", description=f"Deposited **{amount} moneh**!\n💰 Wallet: {user['wallet']} moneh\n🏦 Bank: {user['bank']} moneh", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@tree.command(name="withdraw", description="Withdraw moneh from bank")
@app_commands.describe(amount="Amount to withdraw")
async def withdraw(interaction: discord.Interaction, amount: int):
    user = get_user(interaction.user.id)
    if amount <= 0 or user["bank"] < amount:
        embed = discord.Embed(title="❌ Withdrawal Failed", description="Invalid amount or insufficient bank balance.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    user["wallet"] += amount
    user["bank"] -= amount
    save_data()
    embed = discord.Embed(title="💰 Withdrawal Successful", description=f"Withdrew **{amount} moneh**!\n💰 Wallet: {user['wallet']} moneh\n🏦 Bank: {user['bank']} moneh", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

# -------- Rob Command (wallet can go negative) --------
@tree.command(name="rob", description="Attempt to rob another user (every 2h)")
@app_commands.describe(member="User to rob")
async def rob(interaction: discord.Interaction, member: discord.Member):
    if member.bot:
        await interaction.response.send_message("❌ You cannot rob bots!", ephemeral=True)
        return
    uid = interaction.user.id
    target_uid = member.id
    remaining = check_cooldown(uid, "rob", 7200)
    if remaining > 0:
        embed = discord.Embed(title="⏱ Rob Cooldown", description=f"You must wait {format_cooldown(remaining)} to rob someone.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    user = get_user(uid)
    target = get_user(target_uid)
    chance = random.randint(1,100)
    if chance <= 25:  # success
        percent = random.randint(5,25)
        stolen = int(target["wallet"] * percent / 100)
        target["wallet"] -= stolen
        user["wallet"] += stolen
        set_cooldown(uid, "rob")
        save_data()
        embed = discord.Embed(title="💰 Rob Success!", description=f"You successfully robbed {member.name} and stole **{stolen} moneh**!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:  # failed
        percent = random.randint(1,5)
        lost = int(user["wallet"] * percent / 100)
        user["wallet"] -= lost
        target["wallet"] += lost
        set_cooldown(uid, "rob")
        save_data()
        embed = discord.Embed(title="❌ Rob Failed!", description=f"You were fined **{lost} moneh** which goes to {member.name}\n💰 Wallet may go negative: {user['wallet']}", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

# -------- Owner Only Command --------
@tree.command(name="adjust_balance", description="Owner only: add or remove moneh from a user")
@app_commands.describe(member="Target user", amount="Amount to add (or negative to remove)")
async def adjust_balance(interaction: discord.Interaction, member: discord.Member, amount: int):
    app_info = await bot.application_info()
    owner_id = app_info.owner.id
    if interaction.user.id != owner_id:
        await interaction.response.send_message("❌ You are not the owner!", ephemeral=True)
        return
    user = get_user(member.id)
    user["wallet"] += amount  # can go negative
    save_data()
    embed = discord.Embed(
        title="💰 Balance Adjusted",
        description=f"{member.name}'s wallet has been adjusted by **{amount} moneh**.\n💰 New Wallet: {user['wallet']}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# -------- Leaderboards --------
@tree.command(name="leaderboard_server", description="Top 10 richest users in this server")
async def leaderboard_server(interaction: discord.Interaction):
    guild = interaction.guild
    entries = []
    for uid, info in data.items():
        member = guild.get_member(int(uid))
        if member and not member.bot:
            total = info["wallet"] + info["bank"]
            entries.append((member.display_name, total))
    entries.sort(key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title=f"💰 Server Leaderboard - {guild.name}", color=discord.Color.gold())
    if entries:
        for i, (name, amount) in enumerate(entries[:10], start=1):
            embed.add_field(name=f"{i}. {name}", value=f"{amount:,} moneh", inline=False)
    else:
        embed.description = "No users with moneh data in this server!"
    await interaction.response.send_message(embed=embed)

@tree.command(name="leaderboard_global", description="Top 10 richest users globally")
async def leaderboard_global(interaction: discord.Interaction):
    entries = [(uid, info["wallet"] + info["bank"]) for uid, info in data.items()]
    entries.sort(key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title="🌎 Global Leaderboard", color=discord.Color.gold())
    count = 0
    for uid, amount in entries:
        user = bot.get_user(int(uid))
        if user:
            count += 1
            embed.add_field(name=f"{count}. {user.name}", value=f"{amount:,} moneh", inline=False)
            if count >= 10:
                break
    if count == 0:
        embed.description = "No global users found!"
    await interaction.response.send_message(embed=embed)

# -------- On Ready --------
@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")
    await tree.sync()
    print("Slash commands synced!")

# -------- Run Bot --------
bot.run(os.getenv("TOKEN"))
