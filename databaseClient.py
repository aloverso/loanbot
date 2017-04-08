from pymongo import MongoClient
import os

class User:
    def __init__(self, sender_id):
        self.sender_id = sender_id
        self.tools = []
        self.temp_tools = []
        self.stage = NO_CONTACT

class DatabaseClient():
	def __init__(self):
		MONGO_URI = os.environ['mongo_uri']
		client = MongoClient(MONGO_URI)
		db = client.olinloanbot
		self.users = db.users
		self.tools = db.tool

	def get_all_users(self):
		return self.users.find({})

	def get_all_tools(self):
		return self.tools.find({})

	def find_user(self, field_name, field_value):
		return self.users.find_one({field_name:field_value})

	def find_user_by_sender_id(self, sender_id):
		return self.users.find_one({'sender_id':sender_id})

	def find_or_create_user(self, sender_id):
	    user = self.users.find_one({'sender_id':sender_id})
	    if user == None:
	        user = User(sender_id)
	        self.users.insert_one(user.__dict__)
	    return user

	def update_user(self, updated_user):
		sender_id = updated_user['sender_id']
		self.users.find_one_and_replace({"sender_id":sender_id}, updated_user)

	def find_tool_by_name(self, name):
		return self.tools.find_one({'name':name})

	def find_tool_by_id(self, tool_id):
		return self.tools.find_one({'_id':tool_id})

	def update_tool(self, updated_tool):
		self.tools.find_one_and_replace({"_id":updated_tool['_id']}, updated_tool)