import os
import json
import sys
import requests
from flask import Flask, redirect, render_template, request, url_for, Response
from slackclient import SlackClient
import random
import re
import time
from pymongo import MongoClient
import threading

app = Flask(__name__)

APP_SECRET = os.environ['appSecret']
VALIDATION_TOKEN = os.environ['validationToken']
PAGE_ACCESS_TOKEN = os.environ['pageAccessToken']
SERVER_URL = os.environ['serverURL']
SLACK_TOKEN = os.environ.get('SLACK_TOKEN', None)
SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')
MONGO_URI = os.environ['mongo_uri']

slack_client = SlackClient(SLACK_TOKEN)

ASK_OLIN = 'C4754C6JU'

client = MongoClient(MONGO_URI)
db = client.askolin
users = db.users

# is there a better way to do this than a scheduled interval?
def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

class User:
    def __init__(self, sender_id, name):
        self.sender_id = sender_id
        self.name = name
        self.birthday = int(time.time())
        self.last_message_sent = int(time.time())
        self.last_message_recieved = None

@app.route('/slack', methods=['POST'])
def inbound():
    if request.form.get('token') == SLACK_WEBHOOK_SECRET:
        channel = request.form.get('channel_name')
        username = request.form.get('user_name')
        text = request.form.get('text')

        #Do something with the message here
        inbound_message = "{} in {} says: {}".format(username, channel, text)
        print(inbound_message)
        send_reply(text)

    return Response(), 200

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
                    
                    user = generate_or_find_user(sender_id)
                    name = user['name']

                    if 'text' in messaging_event["message"]:
                        message_text = messaging_event["message"]["text"]  # the message's text

                        send_slack_message(ASK_OLIN, name, message_text, '')

                        send_message(sender_id, "Sent to Oliners! You'll hear back soon!")

                    elif 'attachments' in messaging_event["message"]:
                        attachment_url = messaging_event["message"]["attachments"][0]["payload"]["url"]
                        send_slack_message(ASK_OLIN, name, '', attachment_url)

                        send_message(sender_id, "Sent to Oliners! You'll hear back soon!")

                    else:
                        send_message(sender_id, "Sorry, I can't read that message format!")

    return "ok", 200

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

def list_channels():
    channels_call = slack_client.api_call("channels.list")
    if channels_call['ok']:
        return channels_call['channels']
    return None


def channel_info(channel_id):
    channel_info = slack_client.api_call("channels.info", channel=channel_id)
    if channel_info:
        return channel_info['channel']
    return None

def send_slack_message(channel_id, name, message, attachment_url):
    slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        username=name,
        attachments=[{"image_url":attachment_url, "title":""}],
        icon_emoji=":{}:".format(name[name.index('-')+1:])
    )

def generate_or_find_user(sender_id):
    if users.find_one({"sender_id":sender_id}) == None:

        f = open('names.txt')
        names = f.readlines()
        names = list(map(lambda n: n.strip(), names))
        f.close()

        new_name = names[users.count()]

        new_user = User(sender_id, new_name)

        users.insert_one(new_user.__dict__)

    return users.find_one_and_update(
        {"sender_id":sender_id}, 
        {"last_message_sent":int(time.time())}, 
        return_document=ReturnDocument.AFTER)

def send_reply(slack_message):
    # assuming in form '>name: messsage here'
    if slack_message[0:1] == '@':
        name = re.sub("[^a-zA-Z-]+", "", slack_message[1:slack_message.index(' ')])

        user = users.find_one({"name":name})

        if user != None:
            users.find_one_and_update({"name":name}, {"last_message_recieved":int(time.time())})
            sender_id = user['sender_id']
            send_message(sender_id, slack_message[slack_message.index(' ')+1:])
        else:
            print("can't find the name")
            pass
    else:
        print("doesn't start with @")
        pass

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host=os.environ.get("HOST", '127.0.0.1'))
