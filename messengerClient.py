import os
import json
import requests

'''
A class that interfaces with facebook Messenger and receives and sends message data
'''
class MessengerClient:

    def __init__(self):
        self.PAGE_ACCESS_TOKEN = os.environ['pageAccessToken']

    '''
    handles data received from the webhook
    extracts the message text and sender_id and returns
    '''
    def handle_received_data(self, data):
        print('handing received data')
        if data["object"] == "page":
            print(data['entry'])
            for entry in data["entry"]:
                print('entry:', entry)
                for messaging_event in entry["messaging"]:
                    print('event: ', messaging_event)

                    # someone sent us a message
                    if messaging_event.get("message"):  
                       
                        # the facebook ID of the person sending you the message
                        sender_id = messaging_event["sender"]["id"]
                        
                        #if the message is text, send it to be parsed and find/add/update the user in the db.
                        if 'text' in messaging_event["message"]:
                            message_text = messaging_event["message"]["text"].lower()  # the message's text
                            return message_text, sender_id

                        else:
                            return None, sender_id

                    # button click event
                    if messaging_event.get("postback"):
                        sender_id = messaging_event["sender"]["id"]
                        message_payload = messaging_event["postback"]["payload"]
                        return message_payload, sender_id

    '''
    sends a custom FB message with message_text as the body, allows for quickreply options
    '''
    def send_message(self, recipient_id, message_text, quickreply_options_list):
        quickreply_options = []

        print('sending message')

        if quickreply_options_list:
            for option in quickreply_options_list:
                quickreply_options.append({
                            "content_type":"text",
                            "title":option,
                            "payload":"DEVELOPER_DEFINED_PAYLOAD"
                        })

            params = { "access_token": self.PAGE_ACCESS_TOKEN }
            headers = { "Content-Type": "application/json" }
            data = json.dumps({
                "recipient": {
                    "id": recipient_id
                },
                "message": {
                    "text": message_text,
                    "quick_replies": quickreply_options
                }
            })
            r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
            if r.status_code != 200:
                print(r.status_code, r.text)
        else:
            params = { "access_token": self.PAGE_ACCESS_TOKEN }
            headers = { "Content-Type": "application/json" }
            data = json.dumps({
                "recipient": {
                    "id": recipient_id
                },
                "message": {
                    "text": message_text,
                }
            })
            r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
            if r.status_code != 200:
                print(r.status_code, r.text)

    def send_list(self, recipient_id, tools_list, num):

        elements_list = []
        if num == 0:
            num = len(tools_list)

        print('num: ', num)

        for tool in tools_list[:num]:
            elements_list.append({
                    "title": tool['name'],
                    "subtitle": tool['collection'] 
                })

        print('elements: ', elements_list)

        params = { "access_token": self.PAGE_ACCESS_TOKEN }
        headers = { "Content-Type": "application/json" }
        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "list",
                        "top_element_style": "compact",
                        "elements": elements_list,
                         "buttons": [
                            {
                                "title": "View More",
                                "type": "postback",
                                "payload": "View More"                        
                            }
                        ]  
                    }
                }
            }
        })
        r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
        if r.status_code != 200:
            print(r.status_code, r.text)

       
