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

# stages of checkout process
NO_CONTACT = 0
SENT_GREETING = 1
WANT_CHECKOUT = 2
#IDENTIFY_TOOL = 3
CONFIRM_TOOL = 4
HOW_LONG = 5
CLOSING = 6

class User:
    def __init__(self, sender_id):
        self.sender_id = sender_id
        self.tools = []
        self.temp_tools = []
        self.stage = NO_CONTACT

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
                        message_text = messaging_event["message"]["text"].lower()  # the message's text

                        user = make_or_find_user(sender_id)

                        updated_user = determine_response_and_send(user, message_text)
                        print(updated_user)
                        print(type(updated_user))
                        users.find_one_and_replace({"sender_id":sender_id}, updated_user)

                    elif 'attachments' in messaging_event["message"]:

                        send_message(sender_id, "You sent an attachment")

                    else:
                        send_message(sender_id, "Sorry, I can't read that message format!")

    return "ok", 200

tools = ['screwdriver', 'drill', 'arduino']
checkout_words = ['check out', 'checkout', 'checking out', 'take', 'took', 'taking', 'grabbing', 'grab', 'grabbed', 'checked out', 'borrow', 'borrowed']
greetings = ['hello', 'hi', 'hey', 'sup']

def make_or_find_user(sender_id):
    user = users.find_one({"sender_id":sender_id})
    if user == None:
        user = User(sender_id)
        users.insert_one(user.__dict__)
    return user

def determine_response_and_send(user, message):

    print(user)
    print(user['stage'])

    if user['stage'] == NO_CONTACT:
        # check for checkout words
        if any(word in message for word in checkout_words):
            # id as checkout request
            user['stage'] = WANT_CHECKOUT
        else:
            # send greeting and ask what tool
            send_message(user['sender_id'], "Hi there! I'm the loan bot, what tool would you like to check out?")
            user['stage'] = SENT_GREETING
            return user

    if user['stage'] == WANT_CHECKOUT:
        u = find_tools(user, message)
        print(u)
        return u

    # we sent them a greeting and asked what tool
    if user['stage'] == SENT_GREETING:
        u = find_tools(user, message)
        print(u)
        return u

    if user['stage'] == CONFIRM_TOOL:
        if message == 'yes':
            # for tool in temp_tools:
            #     user['tools'].append(tool)
            time = calculate_time_for_loan(user['temp_tools'])
            send_howlong_quickreply_message(user['sender_id'], "Great! Is a loan time of {} days okay?".format(time))
            user['stage'] = HOW_LONG
            return user
        else:
            send_message(user['sender_id'], "Sorry I misunderstood.  What tool do you want to check out?")
            user['temp_tools'] = []
            user['stage'] = WANT_CHECKOUT
            return user

    if user['stage'] == HOW_LONG:
        tool_string = make_tool_string(user)

        # TODO: update tools due date with response

        send_message(user['sender_id'], "You're all set!  I'll remind you to return the {} before it's due.".format(tool_string))
        user['stage'] = NO_CONTACT
        return user

    print('I GOT TO THE END, OH NO')
    return user

    ## TODO: check for cancelling

def make_tool_string(user):
    tool_string = ''
    for tool in user['temp_tools']:
        user['tools'].append(tool)
        tool_string = tool_string + tool + " and " # allow for a list of tools
    # remove final and from string
    tool_string = tool_string[:-5]
    return tool_string

def find_tools(user, message):
    found_tool = False
    for tool in tools:
        if tool in message:
            found_tool = True
            user['temp_tools'].append(tool)
    if found_tool:
        tool_string = make_tool_string(user)
        send_quickreply_message(user['sender_id'], "Sounds like you want to check out a {}, is that correct?".format(tool_string))
        user['stage'] = CONFIRM_TOOL
        return user
    if not found_tool:
        send_message(user['sender_id'], "What tool do you want to check out?")
        user['stage'] = WANT_CHECKOUT
        return user

# what format for time (start: day)
def calculate_time_for_loan(temp_tools):
    return 1

def send_howlong_quickreply_message(recipient_id, message_text):
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
                    "title":"12 hours instead",
                    "payload":"DEVELOPER_DEFINED_PAYLOAD_12_HOURS"
                },
                {
                    "content_type":"text",
                    "title":"3 days instead",
                    "payload":"DEVELOPER_DEFINED_PAYLOAD_3_DAYS"
                }
            ]
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code, r.text)

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
