import os
import json
import sys
import requests
from flask import Flask, redirect, render_template, request, url_for, Response
from pymongo import MongoClient

app = Flask(__name__)

VALIDATION_TOKEN = os.environ['validationToken']
PAGE_ACCESS_TOKEN = os.environ['pageAccessToken']
MONGO_URI = os.environ['mongo_uri']

client = MongoClient(MONGO_URI)
db = client.olinloanbot
users = db.users
tools = db.tools

class User:
    def __init__(self, sender_id):
        self.sender_id = sender_id
        self.tools = []

class Tool:
    def __init__(self, name):
        self.name = name
        self.current_user = None
        self.current_due_date = None

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
                    
                    if 'quick_reply' in messaging_event['message']:
                        print(messaging_event["message"]["quick_reply"]["payload"])

                    print(messaging_event["message"]["seq"])

                    if 'text' in messaging_event["message"]:
                        message_text = messaging_event["message"]["text"]  # the message's text

                        determine_response_and_send(sender_id, message_text)

                    elif 'attachments' in messaging_event["message"]:

                        send_message(sender_id, "You sent an attachment")

                    else:
                        send_message(sender_id, "Sorry, I can't read that message format!")

    return "ok", 200

tools = ['screwdriver', 'drill', 'arduino']
checkout_words = ['check out', 'checkout', 'checking out', 'take', 'took', 'taking', 'grabbing', 'grab', 'grabbed', 'checked out']

def determine_response_and_send(sender_id, message):
    if any(word in message for word in checkout_words):
        found_tool = False
        for tool in tools:
            if tool in message:
                found_tool = True
                send_quickreply_message(sender_id, "Sounds like you want to check out a {}, is that correct?".format(tool))
        if not found_tool:
            send_message(sender_id, "What tool do you want to check out?")
    else:
        send_message(sender_id, "idk what you're sayin yo:" + message)

def send_quickreply_message(recipient_id, message_text):
    params = { "access_token": PAGE_ACCESS_TOKEN }
    headers = { "Content-Type": "application/json" }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text,
            "quick_replies":[
                {
                    "content_type":"text",
                    "title":"yes",
                    "payload":"DEVELOPER_DEFINED_PAYLOAD_YES"
                },
                {
                    "content_type":"text",
                    "title":"no",
                    "payload":"DEVELOPER_DEFINED_PAYLOAD_NO"
                }
            ]
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code, r.text)

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
