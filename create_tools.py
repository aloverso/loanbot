import os
from pymongo import MongoClient

MONGO_URI = os.environ['mongo_uri']

client = MongoClient(MONGO_URI)
db = client.olinloanbot
tools = db.tools

class Tool:
    def __init__(self, name):
        self.name = name
        self.current_user = None
        self.current_due_date = None

tools_list = [Tool('screwdriver'), Tool('drill'), Tool('arduino')]

def create_tools(tools_list):
	for tool in tools_list:
		tools.insert_one(tool.__dict__)
create_tools(tools_list)