from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Get configuration from environment variables for security
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_verify_token")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "YOUR_PERMANENT_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "YOUR_PHONE_NUMBER_ID")

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Verification challenge
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403

    elif request.method == "POST":
        data = request.get_json()
        print("Incoming webhook data:", data)

        if data and "entry" in data:
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for message in messages:
                        from_number = message["from"]  # sender's WhatsApp number
                        text = message.get("text", {}).get("body")

                        print(f"Message from {from_number}: {text}")

                        # Send an auto-reply
                        send_whatsapp_message(from_number, f"Welcome to our Jharkhand Tourism Service!\n Your Query: {text}")

        return jsonify({"status": "received"}), 200


def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Reply status:", response.status_code, response.text)


if __name__ == "__main__":
    # Use environment variables for production deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
# A simple Flask app to handle Meta (Facebook) webhook verification and incoming messages.