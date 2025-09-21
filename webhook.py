from flask import Flask, request, jsonify
import requests
import qrcode
import io
import os

app = Flask(__name__)

# Get configuration from environment variables for security
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_verify_token")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "YOUR_PERMANENT_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "YOUR_PHONE_NUMBER_ID")

# Jharkhand tourist attractions
PLACES = {
    "1": "Baba Baidyanath Temple, Deoghar",
    "2": "Dassam Falls, Ranchi",
    "3": "Patratu Valley, Ranchi",
    "4": "Parasnath Hills, Giridih",
    "5": "Netarhat, Latehar",
    "6": "Jonha Falls, Ranchi",
    "7": "Betla National Park & Palamu Fort"
}

# Track user conversation state
user_state = {}

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "service": "Jharkhand Tourism WhatsApp Webhook",
        "version": "1.0"
    }), 200

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
                        text = message.get("text", {}).get("body", "").strip().lower()

                        print(f"Message from {from_number}: {text}")

                        if "book ticket" in text:
                            user_state[from_number] = "choosing_place"
                            place_list = "\n".join([f"{k}. {v}" for k, v in PLACES.items()])
                            send_whatsapp_message(from_number,
                                f"Welcome to Jharkhand Tourism 🎉\nPlease choose a place by typing its number:\n\n{place_list}")

                        elif user_state.get(from_number) == "choosing_place" and text in PLACES:
                            place = PLACES[text]
                            qr_data = f"E-Ticket confirmed for {place}"
                            qr_image_id = upload_qr_code(qr_data)
                            if qr_image_id:
                                send_whatsapp_qr(from_number, qr_image_id, place)
                            else:
                                send_whatsapp_message(from_number, "Could not generate QR code ❌")
                            user_state[from_number] = None

                        else:
                            send_whatsapp_message(from_number, f"Welcome to Jharkhand Tourism! 🌟\nType 'book ticket' to start booking your adventure.")

        return jsonify({"status": "received"}), 200


def upload_qr_code(data):
    """Generate QR code and upload to WhatsApp Cloud API, return media_id"""
    try:
        # Generate QR code in memory
        qr = qrcode.make(data)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)

        # Upload to WhatsApp Cloud API
        upload_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/media"
        files = {"file": ("qrcode.png", buf, "image/png")}
        payload = {"messaging_product": "whatsapp"}
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

        response = requests.post(upload_url, headers=headers, files=files, data=payload)
        print("Upload response:", response.status_code, response.text)

        if response.status_code == 200:
            return response.json().get("id")
        else:
            print(f"Upload failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error generating/uploading QR code: {str(e)}")
        return None


def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Text reply:", response.status_code, response.text)


def send_whatsapp_qr(to, media_id, place=None):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    caption = f"Here is your e-ticket QR for {place} 🎟️✨" if place else "Here is your e-ticket QR 🎟️"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"id": media_id, "caption": caption}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("QR reply:", response.status_code, response.text)


if __name__ == "__main__":
    # Use environment variables for production deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
# A simple Flask app to handle Meta (Facebook) webhook verification and incoming messages.