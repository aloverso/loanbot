import os
import json
import sys
import requests
from flask import Flask, redirect, render_template, request, url_for, Response

app = Flask(__name__)

VALIDATION_TOKEN = os.environ['validationToken']
PAGE_ACCESS_TOKEN = os.environ['pageAccessToken']

@app.route('/')
def home():
    return 'ok'

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VALIDATION_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

@app.route('/webhook', methods=['POST'])
def posthook():

    data = request.get_json()

    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    
                    if 'text' in messaging_event["message"]:
                        message_text = messaging_event["message"]["text"]  # the message's text

                        send_message(sender_id, determine_response(message_text))

                    elif 'attachments' in messaging_event["message"]:

                        send_message(sender_id, "You sent an attachment")

                    else:
                        send_message(sender_id, "Sorry, I can't read that message format!")

    return "ok", 200

tools = ['screwdriver']
checkout_words = ['check out', 'checkout', 'checking out', 'take', 'took', 'checked out']

def determine_response(message):
    if any(word in message for word in checkout_words):
        return "you're checking something out"
    else:
        "idk what you're sayin yo"

def send_message(recipient_id, message_text):
    params = { "access_token": PAGE_ACCESS_TOKEN }
    headers = { "Content-Type": "application/json" }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code, r.text)

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host=os.environ.get("HOST", '127.0.0.1'))
