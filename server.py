import os
from flask import Flask, redirect, render_template, request, url_for, Response
from apscheduler.schedulers.background import BackgroundScheduler

import messengerClient
import conversationHandler
import databaseClient

app = Flask(__name__)

VALIDATION_TOKEN = os.environ['validationToken']


REMINDER_TIME = 60 # should be 2 hours
INTERVAL_TIME = 30 # should be 1 hour

messenger_client = messengerClient.MessengerClient()
database_client = databaseClient.DatabaseClient()
conversation_handler = conversationHandler.ConversationHandler(database_client)

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

    print('posthook')
    message_text, sender_id = messenger_client.handle_received_data(data)
    user = database_client.find_or_create_user(sender_id)
    
    updated_user, response, quickreply = conversation_handler.determine_response_for_user(message_text, user)
    database_client.update_user(updated_user)
    print('response: ', response)
    messenger_client.send_message(updated_user['sender_id'], response, quickreply)
    

    return "ok", 200

def check_if_due_and_remind():
    '''
    loops through the tools to determine whether they are due 
    in the next two hours, and sends the reminder to the user. uses import time
    '''
    print('beginning check_if_due_and_remind')
    current_time = int(time.time())
    tools_list = tools.find({})
    for tool in tools_list:
        print('next tool')
        if tool['current_due_date']:
            print('tool had due date')
            if int(tool['current_due_date'])-current_time<=(REMINDER_TIME):
                reminder_message = 'Hi! The {} is due very soon, could you bring it back to the library please?'.format(tool['name'])
                user_to_remind = users.find_one({'_id':tool['current_user']})
                send_message(user_to_remind['sender_id'], reminder_message)
                print('sent reminder message for {}'.format(tool['_id']))

#TODO: let them say they have returned it, so it stops reminding them

apsched = BackgroundScheduler()
apsched.start()
apsched.add_job(check_if_due_and_remind, 'interval', seconds=INTERVAL_TIME)

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host=os.environ.get("HOST", '127.0.0.1'))