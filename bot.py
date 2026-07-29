import discord
from discord.ext import commands
import stripe
import os
import threading

from flask import Flask, request
from dotenv import load_dotenv


load_dotenv()


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# -----------------------------
# Discord setup
# -----------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# -----------------------------
# Stripe webhook
# -----------------------------

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():

    event = request.json

    print("Stripe event:", event["type"])


    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        discord_id = int(
            session["metadata"]["discord_id"]
        )

        product = session["metadata"]["product"]


        print(
            "Payment received:",
            discord_id,
            product
        )


        bot.loop.create_task(
            give_role(
                discord_id,
                product
            )
        )


    return "OK"



async def give_role(discord_id, product):

    guild = bot.get_guild(
        int(os.getenv("GUILD_ID"))
    )


    if guild is None:
        print("Guild not found")
        return


    member = guild.get_member(
        discord_id
    )


    if member is None:
        print("Member not found")
        return



    if product == "Lifetime Access":

        role_id = os.getenv(
            "LIFETIME_ROLE_ID"
        )


    elif product == "Monthly Access":

        role_id = os.getenv(
            "MONTH_ROLE_ID"
        )


    elif product == "Weekly Access":

        role_id = os.getenv(
            "WEEK_ROLE_ID"
        )


    else:
        print("Unknown product")
        return



    role = guild.get_role(
        int(role_id)
    )


    if role:

        await member.add_roles(role)

        print(
            "Added role:",
            role.name
        )



# -----------------------------
# Purchase buttons
# -----------------------------

class PurchaseButton(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    async def create_payment(
        self,
        interaction,
        price_id,
        product_name
    ):


        await interaction.response.defer(
            ephemeral=True
        )


        try:

            session = stripe.checkout.Session.create(

                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1
                    }
                ],

                mode="payment",

                success_url=
                "https://example.com/success",

                cancel_url=
                "https://example.com/cancel",

                metadata={

                    "discord_id":
                    str(interaction.user.id),

                    "product":
                    product_name
                }
            )


            await interaction.followup.send(

                f"✅ Pay here:\n{session.url}",

                ephemeral=True
            )


        except Exception as e:

            print("STRIPE ERROR:")
            print(e)


            await interaction.followup.send(

                "❌ Failed creating payment link.",

                ephemeral=True
            )



    @discord.ui.button(
        label="Lifetime",
        style=discord.ButtonStyle.green,
        custom_id="lifetime_button"
    )
    async def lifetime(
        self,
        interaction,
        button
    ):

        await self.create_payment(

            interaction,

            os.getenv(
                "LIFETIME_PRICE_ID"
            ),

            "Lifetime Access"
        )



    @discord.ui.button(
        label="Month",
        style=discord.ButtonStyle.blurple,
        custom_id="month_button"
    )
    async def month(
        self,
        interaction,
        button
    ):

        await self.create_payment(

            interaction,

            os.getenv(
                "MONTH_PRICE_ID"
            ),

            "Monthly Access"
        )



    @discord.ui.button(
        label="Week",
        style=discord.ButtonStyle.gray,
        custom_id="week_button"
    )
    async def week(
        self,
        interaction,
        button
    ):

        await self.create_payment(

            interaction,

            os.getenv(
                "WEEK_PRICE_ID"
            ),

            "Weekly Access"
        )



# -----------------------------
# Bot events
# -----------------------------

@bot.event
async def on_ready():

    print(
        f"Logged in as {bot.user}"
    )


    bot.add_view(
        PurchaseButton()
    )



@bot.command()
async def shop(ctx):


    embed = discord.Embed(

        title="⭐ Instant Access",

        description=
        "Purchase below for instant access!\n\n"
        "Choose your plan:",

        color=0x00ff00
    )


    embed.add_field(

        name="Lifetime",

        value="Permanent access",

        inline=False
    )


    embed.add_field(

        name="Month",

        value="30 days access",

        inline=False
    )


    embed.add_field(

        name="Week",

        value="7 days access",

        inline=False
    )


    embed.set_footer(

        text="Payments securely handled by Stripe"

    )


    await ctx.send(

        embed=embed,

        view=PurchaseButton()

    )



# -----------------------------
# Start webhook server
# -----------------------------

def run_webhook():

    app.run(

        host="0.0.0.0",

        port=5000

    )



threading.Thread(

    target=run_webhook,

    daemon=True

).start()



# -----------------------------
# Start bot
# -----------------------------

bot.run(
    os.getenv("DISCORD_TOKEN")
)