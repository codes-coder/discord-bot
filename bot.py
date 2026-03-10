import discord
from discord.ext import commands
import random

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

deck = [
("A♠",11),("2♠",2),("3♠",3),("4♠",4),("5♠",5),("6♠",6),("7♠",7),("8♠",8),("9♠",9),("10♠",10),("J♠",10),("Q♠",10),("K♠",10),
("A♥",11),("2♥",2),("3♥",3),("4♥",4),("5♥",5),("6♥",6),("7♥",7),("8♥",8),("9♥",9),("10♥",10),("J♥",10),("Q♥",10),("K♥",10),
("A♦",11),("2♦",2),("3♦",3),("4♦",4),("5♦",5),("6♦",6),("7♦",7),("8♦",8),("9♦",9),("10♦",10),("J♦",10),("Q♦",10),("K♦",10),
("A♣",11),("2♣",2),("3♣",3),("4♣",4),("5♣",5),("6♣",6),("7♣",7),("8♣",8),("9♣",9),("10♣",10),("J♣",10),("Q♣",10),("K♣",10)
]

def hand_value(hand):
    value = sum(card[1] for card in hand)
    aces = sum(1 for card in hand if card[1] == 11)

    while value > 21 and aces:
        value -= 10
        aces -= 1

    return value


class BlackjackView(discord.ui.View):

    def __init__(self, player, dealer):
        super().__init__(timeout=60)
        self.player = player
        self.dealer = dealer

    def player_cards(self):
        return " ".join(card[0] for card in self.player)

    def dealer_cards(self):
        return " ".join(card[0] for card in self.dealer)


    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.player.append(random.choice(deck))
        value = hand_value(self.player)

        if value > 21:
            await interaction.response.edit_message(
                content=f"🃏 Your cards: {self.player_cards()} ({value})\n💥 Bust! You lose.",
                view=None
            )
            return

        await interaction.response.edit_message(
            content=f"🃏 Your cards: {self.player_cards()} ({value})",
            view=self
        )


    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):

        while hand_value(self.dealer) < 17:
            self.dealer.append(random.choice(deck))

        player_value = hand_value(self.player)
        dealer_value = hand_value(self.dealer)

        if dealer_value > 21 or player_value > dealer_value:
            result = "🎉 You win!"
        elif dealer_value == player_value:
            result = "🤝 Tie!"
        else:
            result = "😢 Dealer wins!"

        await interaction.response.edit_message(
            content=f"🃏 Your cards: {self.player_cards()} ({player_value})\nDealer: {self.dealer_cards()} ({dealer_value})\n{result}",
            view=None
        )


@bot.command()
async def blackjack(ctx):

    player = [random.choice(deck), random.choice(deck)]
    dealer = [random.choice(deck), random.choice(deck)]

    view = BlackjackView(player, dealer)

    await ctx.send(
        f"🃏 Blackjack\nYour cards: {' '.join(card[0] for card in player)} ({hand_value(player)})\nDealer shows: {dealer[0][0]}",
        view=view
    )


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")


bot.run("MTQ4MDc2MDk1MDM1NjQ0MzI2Ng.GdHGch.a0j4I-8V8y9laGHdJ4b-SdidBRP0fcwiJlJMe0")
