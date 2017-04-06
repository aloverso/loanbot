import os
import json
import sys
import requests
from flask import Flask, redirect, render_template, request, url_for, Response
from pymongo import MongoClient
import time
import threading

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


REMINDER_TIME = 60 # should be 2 hours
INTERVAL_TIME = 30 # should be 1 hour

class User:
    def __init__(self, sender_id):
        self.sender_id = sender_id
        self.tools = []
        self.temp_tools = []
        self.stage = NO_CONTACT

# class Tool:
#     def __init__(self, name):
#         self.name = name
#         self.current_user = None
#         self.current_due_date = None

checkout_words = ['check out', 'checkout', 'checking out', 'take', 'took', 'taking', 'grabbing', 'grab', 'grabbed', 'checked out', 'borrow', 'borrowed']
greetings = ['hello', 'hi', 'hey', 'sup']
return_words = ['return', 'returned','returning','brought', 'bring', 'bringing', 'dropping', 'dropped', 'took back', 'left', 'done', 'done with', 'finished']
@app.route('/')
def home():
    return 'ok'

@app.route('/webhook', methods=['GET'])
def verify():
    '''
    Facebook (FB) validating that we are in control of the app. 
    '''
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VALIDATION_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

@app.route('/webhook', methods=['POST'])
def posthook():
    '''
    Runs when we receive a message from FB, includes the FB message 
    data and metadata. The entry point to our other functions.
    '''
    #handles the request and gets us into the current message
    data = request.get_json()

    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                # someone sent us a message
                if messaging_event.get("message"):  
                    # the facebook ID of the person sending you the message
                    sender_id = messaging_event["sender"]["id"]        
                    # the recipient's ID, which should be your page's facebook ID
                    recipient_id = messaging_event["recipient"]["id"]  
                    #for testing, what we get when we receive a quick reply
                    if 'quick_reply' in messaging_event['message']:
                        print(messaging_event["message"]["quick_reply"]["payload"])
                    #if the message is text, send it to be parsed and find/add/update the user in the db.
                    if 'text' in messaging_event["message"]:
                        message_text = messaging_event["message"]["text"].lower()  # the message's text

                        user = make_or_find_user(sender_id)

                        updated_user = determine_response_and_send(user, message_text)
                        # print(updated_user)
                        # print(type(updated_user))
                        users.find_one_and_replace({"sender_id":sender_id}, updated_user)
                    #we don't currently do anything with attachments
                    elif 'attachments' in messaging_event["message"]:

                        send_message(sender_id, "You sent an attachment")
                    #anything else (?) we are sorry we can't read
                    else:
                        send_message(sender_id, "Sorry, I can't read that message format!")

    return "ok", 200

def set_interval(func, sec):
    '''
    creates a timer that runs a function (func) after every sec seconds. uses import threading
    FOR SOME REASON THIS IS RUNNING DOUBLE, BUT ONLY HERE, NOT IN TESTING
    '''
    def func_wrapper():
        print('delving into func_wrapper')
        set_interval(func, sec)
        print('func_wrapper after set_interval')
        func()
    t=threading.Timer(sec, func_wrapper)
    t.start()
    return t

def check_if_due_and_remind():
    '''
    loops through the tools to determine whether they are due 
    in the next two hours, and sends the reminder to the user. uses import time
    '''
    print('beginning check_if_due_and_remind')
    # current_time = int(time.time())
    # tools_list = tools.find({})
    # for tool in tools_list:
    #     print('next tool')
    #     if tool['current_due_date']:
    #         print('tool had due date')
    #         if int(tool['current_due_date'])-current_time<=(REMINDER_TIME):
    #             reminder_message = 'Hi! The {} is due very soon, could you bring it back to the library please?'.format(tool['name'])
    #             user_to_remind = users.find_one({'_id':tool['current_user']})
    #             send_message(user_to_remind['sender_id'], reminder_message)
    #             print('sent reminder message for {}'.format(tool['_id']))
#TODO: let them say they have returned it, so it stops reminding them

set_interval(check_if_due_and_remind, INTERVAL_TIME)

def make_or_find_user(sender_id):
    '''
    Makes or finds the user in the db by FB sender ID, returns user
    '''
    user = users.find_one({'sender_id':sender_id})
    if user == None:
        user = User(sender_id)
        users.insert_one(user.__dict__)
    return user

def determine_response_and_send(user, message):
    '''
    Uses the user's stage to parse the message and determine how to reply
    '''
    # print(user)
    print(user['stage'])
    #if the user is initiating contact
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

    #if the user wants to check out something
    if user['stage'] == WANT_CHECKOUT:
        u = find_tools(user, message)
        # print(u)
        return u

    # we sent them a greeting and asked what tool
    if user['stage'] == SENT_GREETING:
        #for now, passing in checking out use case. can be adapted to other use cases in the future.
        u = find_tools(user, message)
        # print(u)
        return u

    #we check that we parsed the correct tool/s...
    if user['stage'] == CONFIRM_TOOL:

        #...if so, we find out how long the loan will be
        if message == 'yes':
            # for tool in temp_tools:
            #     user['tools'].append(tool)
            time = calculate_time_for_loan(user['temp_tools'])
            send_howlong_quickreply_message(user['sender_id'], "Great! Is a loan time of {} days okay?".format(time))
            user['stage'] = HOW_LONG
            return user

        #...if not, we try again
        else:
            send_message(user['sender_id'], "Sorry I misunderstood.  What tool do you want to check out?")
            user['temp_tools'] = []
            user['stage'] = WANT_CHECKOUT
            return user

    #update user and tool db based on the loan time
    if user['stage'] == HOW_LONG:
        tool_string = make_tool_string(user)
        for tool in user['temp_tools']:
            tool['current_user'] = user['_id']
            tool['current_due_date'] = parse_due_date(message)
            tools.find_one_and_replace({'_id':tool['_id']},tool)
            user['tools'].append(tool['_id'])

        # TODO: how to handle loan time if they are checking out more than one tool

        #finish the interaction and reset the conversation stage
        send_message(user['sender_id'], "You're all set!  I'll remind you to return the {} before it's due.".format(tool_string))
        user['temp_tools'] = []
        user['stage'] = NO_CONTACT
        return user

    #check if the user is trying to say they have returned a tool
    if any(word in message for word in return_words):
        tools_checked_out_by_user = []
        for tool_id in user['tools']:
            tools_checked_out_by_user.append(tools.find_one({'_id':tool_id})['name'])


    print('I GOT TO THE END, OH NO')
    return user

    ## TODO: check for cancelling
def parse_due_date(message):
    '''
    Parses the loan time quick reply message to store a due_date 
    for the tool/s the user wants to check out. uses import time
    '''
    due_date = 0
    SECONDS_IN_DAY = 3600*24

    # they want a 24 hour loan
    if message == 'yes':
        due_date = int(time.time()) + 120 # !!!!!! CHANGE THIS BACK TO SECONDS_IN_DAY!!!!!!
    # they want a 12 hour loan
    elif message == '12 hours instead':
        due_date = int(time.time()) + (SECONDS_IN_DAY/2)
    #they want a 3 day loan
    elif message == '3 days instead':
        due_date = int(time.time()) + (SECONDS_IN_DAY*3)
    return due_date


def make_tool_string(user):
    '''
    creates a string of all tools a user is attempting to check out
    '''
    tool_string = ''
    for tool in user['temp_tools']:
        tool_string = tool_string + tool['name'] + " and " # allow for a list of tools
    # remove final and from string
    tool_string = tool_string[:-5]
    return tool_string

def find_tools(user, message):
    '''
    parses a message for tool/s to be checked out 
    '''
    found_tool = False
    tools_list = tools.find({})

    #loop through list looking for tool names in message
    for tool in tools_list:
        if tool['name'] in message:
            found_tool = True
            user['temp_tools'].append(tool)

    #if we found a tool name/s in the message
    if found_tool:
        tool_string = make_tool_string(user)
        send_quickreply_message(user['sender_id'], "Sounds like you want to check out a {}, is that correct?".format(tool_string))
        user['stage'] = CONFIRM_TOOL
        return user

    #if we could not identify a tool name/s in the message
    if not found_tool:
        send_message(user['sender_id'], "What tool do you want to check out?")
        user['stage'] = WANT_CHECKOUT
        return user


# what format for time (start: day)
def calculate_time_for_loan(temp_tools):
    return 1

def send_howlong_quickreply_message(recipient_id, message_text):
    '''
    sends a FB quick reply message with options for loan time. 
    the options are yes (1 day), 12 hours instead, 3 days instead
    '''
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
    '''
    sends a FB quick reply message with yes/no options
    '''
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
    '''
    sends a custom FB message with message_text as the body
    '''
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
