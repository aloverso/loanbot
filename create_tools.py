import os
from pymongo import MongoClient

MONGO_URI = os.environ['mongo_uri']

client = MongoClient(MONGO_URI)
db = client.olinloanbot
tools = db.tools

class Tool:
    def __init__(self, name, collection, resource_link):
        self.name = name
        self.current_user = None
        self.current_due_date = None
        self.collection = collection
        self.resource_link = resource_link

tools_list = [Tool('screwdriver', 'tool wall', None), 
Tool('drill', 'tool wall', None), 
Tool('arduino', 'tool wall', 'https://www.arduino.cc/en/Main/Docs'), 
Tool('camera','media', 'https://vimeo.com/201067762'), 
Tool('tripod', 'media', 'https://vimeo.com/201067762'),
Tool('lens', 'media', 'https://vimeo.com/201067762')]

def create_tools(tools_list):
	for tool in tools_list:
		tools.insert_one(tool.__dict__)
create_tools(tools_list)