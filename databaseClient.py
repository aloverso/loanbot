from pymongo import MongoClient
import os

'''
the class sructure used for the User in the Mongo database
'''
class User:
    def __init__(self, sender_id):
        self.sender_id = sender_id
        self.tools = []
        self.temp_tools = []
        self.stage = 0

'''
A client which connects to Mongo and deals with Mongo database operations
'''
class DatabaseClient():
	def __init__(self):
		MONGO_URI = os.environ['mongo_uri']
		client = MongoClient(MONGO_URI)
		db = client.olinloanbot
		self.users = db.users
		self.tools = db.tools

	'''
	returns all users in the Users database
	'''
	def get_all_users(self):
		return self.users.find({})

	'''
	returns all tools in the Tools database
	'''
	def get_all_tools(self):
		return self.tools.find({})

	'''
	finds a user from a given field, allowing to search by any field
	'''
	def find_user(self, field_name, field_value):
		return self.users.find_one({field_name:field_value})

	'''
	finds one user by using the sender_id as the search field
	'''
	def find_user_by_sender_id(self, sender_id):
		return self.users.find_one({'sender_id':sender_id})

	'''
	either finds a user by sender_id, or creates that user in the database
	returns the user
	'''
	def find_or_create_user(self, sender_id):
	    user = self.users.find_one({'sender_id':sender_id})
	    if user == None:
	        user = User(sender_id)
	        self.users.insert_one(user.__dict__)
	    user = self.users.find_one({'sender_id':sender_id})
	    return user

	'''
	given an updated user dictionary with the same sender_id,
	replaces the old database entry with the new one
	'''
	def update_user(self, updated_user):
		sender_id = updated_user['sender_id']
		self.users.find_one_and_replace({"sender_id":sender_id}, updated_user)

	'''
	finds a tool by searching on the name field
	'''
	def find_tool_by_name(self, name):
		return self.tools.find_one({'name':name})

	'''
	finds a tool by searching on the id field
	'''
	def find_tool_by_id(self, tool_id):
		return self.tools.find_one({'_id':tool_id})

	'''
	given an updated tool dictionary with the same _id,
	replaces the old database entry with the new one
	'''
	def update_tool(self, updated_tool):
		self.tools.find_one_and_replace({"_id":updated_tool['_id']}, updated_tool)