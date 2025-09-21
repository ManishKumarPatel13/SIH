from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Get verify token from environment variable for security
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_verify_token")

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Verification challenge from Meta
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("Webhook verified!")
            return challenge, 200
        else:
            return "Verification failed", 403

    elif request.method == "POST":
        # Incoming messages
        data = request.get_json()
        print("Incoming webhook data:", data)

        # Example: extract message text if present
        if data and "entry" in data:
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for message in messages:
                        from_number = message["from"]
                        text = message.get("text", {}).get("body")
                        print(f"Message from {from_number}: {text}")

        return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    # Use environment variables for production deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
# A simple Flask app to handle Meta (Facebook) webhook verification and incoming messages.