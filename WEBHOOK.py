from flask import Flask, request
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@app.route("/webhook", methods=["POST"])
def webhook():

    event = request.json

    print("Stripe event received:", event["type"])


    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        discord_id = session["metadata"]["discord_id"]

        print("✅ PAYMENT COMPLETE")
        print("Discord User ID:", discord_id)


        # Later we will add:
        # - give Discord role
        # - send confirmation message
        # - save purchase to database


    return "OK"


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )