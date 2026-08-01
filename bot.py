import discord
from discord.ext import commands
from dotenv import load_dotenv

import stripe
import os
import threading

from flask import Flask, request


load_dotenv()


# =====================
# ENV SETTINGS
# =====================

TOKEN = os.getenv("DISCORD_TOKEN")

stripe.api_key = os.getenv(
    "STRIPE_SECRET_KEY"
)


GUILD_ID = int(
    os.getenv("GUILD_ID")
)

CUSTOMER_ROLE_ID = int(
    os.getenv("CUSTOMER_ROLE_ID")
)


DISCORD_INVITE = os.getenv(
    "DISCORD_INVITE"
)


# Stripe prices

PRODUCTS = {

    "Lifetime": {

        "price":
        os.getenv("LIFETIME_PRICE_ID"),

        "key_file":
        "lifetime_keys.txt"

    },


    "Month": {

        "price":
        os.getenv("MONTH_PRICE_ID"),

        "key_file":
        "month_keys.txt"

    },


    "Week": {

        "price":
        os.getenv("WEEK_PRICE_ID"),

        "key_file":
        "week_keys.txt"

    }

}



# =====================
# DISCORD SETUP
# =====================


intents = discord.Intents.default()

intents.message_content = True

intents.members = True


bot = commands.Bot(

    command_prefix="!",

    intents=intents

)



# =====================
# STRIPE CHECKOUT
# =====================


class ShopButtons(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    async def create_checkout(

        self,

        interaction,

        product_name

    ):


        product = PRODUCTS[product_name]


        await interaction.response.defer(
            ephemeral=True
        )


        try:

            session = stripe.checkout.Session.create(


                line_items=[

                    {

                        "price":
                        product["price"],

                        "quantity": 1

                    }

                ],


                mode="payment",


                success_url=
                DISCORD_INVITE,


                cancel_url=
                DISCORD_INVITE,


                metadata={


                    "discord_id":
                    str(interaction.user.id),


                    "product":
                    product_name


                }

            )


            await interaction.followup.send(

                f"💳 Complete your payment here:\n{session.url}",

                ephemeral=True

            )


        except Exception as e:


            print(
                "STRIPE ERROR:"
            )

            print(e)


            await interaction.followup.send(

                "❌ Could not create payment link.",

                ephemeral=True

            )



    @discord.ui.button(

        label="Lifetime",

        style=discord.ButtonStyle.gray,

        custom_id="lifetime_purchase"

    )
    async def lifetime(

        self,

        interaction,

        button

    ):

        await self.create_checkout(

            interaction,

            "Lifetime"

        )



    @discord.ui.button(

        label="Month",

        style=discord.ButtonStyle.gray,

        custom_id="month_purchase"

    )
    async def month(

        self,

        interaction,

        button

    ):

        await self.create_checkout(

            interaction,

            "Month"

        )



    @discord.ui.button(

        label="Week",

        style=discord.ButtonStyle.gray,

        custom_id="week_purchase"

    )
    async def week(

        self,

        interaction,

        button

    ):

        await self.create_checkout(

            interaction,

            "Week"

        )



# =====================
# SHOP COMMAND
# =====================


@bot.command()

async def shop(ctx):


    embed = discord.Embed(

        title="⭐ Purchase Access",

        description=

        "Purchase below for instant access.\n\n"

        "Choose your plan:",

        colour=0xF2F3F5

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


    await ctx.send(

        embed=embed,

        view=ShopButtons()

    )



# =====================
# READY
# =====================


@bot.event

async def on_ready():

    print(
        f"Logged in as {bot.user}"
    )


    bot.add_view(
        ShopButtons()
    )
# =====================
# KEY SYSTEM
# =====================


def get_key(filename):

    try:

        with open(filename, "r") as file:

            keys = file.readlines()


        if len(keys) == 0:

            return None


        key = keys[0].strip()


        with open(filename, "w") as file:

            file.writelines(keys[1:])


        return key


    except FileNotFoundError:

        print(
            f"Missing file: {filename}"
        )

        return None



# =====================
# PAYMENT HANDLER
# =====================


async def complete_purchase(
    discord_id,
    product_name
):


    guild = bot.get_guild(
        GUILD_ID
    )


    if guild is None:

        print(
            "Guild not found"
        )

        return



    member = guild.get_member(
        int(discord_id)
    )


    if member is None:

        print(
            "Member not found"
        )

        return



    # Give Customer role

    role = guild.get_role(
        CUSTOMER_ROLE_ID
    )


    if role:

        await member.add_roles(
            role
        )


    # Get key

    key_file = PRODUCTS[product_name]["key_file"]


    key = get_key(
        key_file
    )


    if key is None:

        key = "No keys available. Contact support."



    # DM user

    try:

        await member.send(

            f"""
✅ Payment successful!

Product:
**{product_name}**

Your Customer role has been added.

Your key:


{key}


Thank you for your purchase!
"""

        )


    except discord.Forbidden:


        print(
            "Could not DM user"
        )



    # Optional channel log

    print(

        f"{member} purchased {product_name}"

    )



# =====================
# FLASK WEBHOOK
# =====================


app = Flask(__name__)



@app.route(
    "/webhook",
    methods=["POST"]
)

def stripe_webhook():


    event = request.json


    print(
        "Stripe event:",
        event["type"]
    )



    if event["type"] == "checkout.session.completed":


        session = event["data"]["object"]


        discord_id = session["metadata"]["discord_id"]


        product = session["metadata"]["product"]



        bot.loop.create_task(

            complete_purchase(

                discord_id,

                product

            )

        )



    return "OK"



# =====================
# START FLASK
# =====================


def run_flask():


    app.run(

        host="0.0.0.0",

        port=5000

    )



threading.Thread(

    target=run_flask,

    daemon=True

).start()



# =====================
# START BOT
# =====================


bot.run(
    TOKEN
)