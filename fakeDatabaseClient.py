import os

'''
the class sructure used for the User in the Mongo database
'''
tools_list = [
{
	"_id":{
		"$oid": "58e5528dbf24551abe30660f"
	},
	"current_user": {
		"$oid": "58ebabe3638acc000b2e2429"
	},
	"name": "screwdriver",
	"current_due_date": 1492100080
},
{
    "_id": {
        "$oid": "58e5528dbf24551abe306610"
    },
    "current_due_date": 1491424505,
    "name": "drill",
    "current_user": {
        "$oid": "58dfe761db78bb000bf7c88b"
    }
},
{
    "_id": {
        "$oid": "58e5528dbf24551abe306611"
    },
    "name": "arduino",
    "current_due_date": None,
    "current_user": None
}]

users_list = [
{
    "_id": {
        "$oid": "58ebabe3638acc000b2e2429"
    },
    "sender_id": "1346430625424620",
    "tools": [
        {
            "$oid": "58e5528dbf24551abe30660f"
        }
    ],
    "stage": 0,
    "temp_tools": []
}]

class User:
    def __init__(self, sender_id):
        self.sender_id = sender_id
        self.tools = []
        self.temp_tools = []
        self.stage = 0

'''
A client which connects to Mongo and deals with Mongo database operations
'''
class fakeDatabaseClient():
	'''
	fake version of get_all_users
	'''
	def get_all_users(self):
		return users_list

	'''
	fake version of get_all_tools
	'''
	def get_all_tools(self):
		return tools_list

	'''
	fake version of find_user
	'''
	def find_user(self, field_name, field_value):
		return None

	'''
	fake version of find_user_by_sender_id
	'''
	def find_user_by_sender_id(self, sender_id):
		return None

	'''
	fake version of find_or_create_user
	'''
	def find_or_create_user(self, sender_id, name):
	    return users_list[0]

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
		return None
		# return self.tools.find_one({'name':name})

	'''
	finds a tool by searching on the id field
	'''
	def find_tool_by_id(self, tool_id):
		return None
		# return self.tools.find_one({'_id':tool_id})

	'''
	given an updated tool dictionary with the same _id,
	replaces the old database entry with the new one
	'''
	def update_tool(self, updated_tool):
		return None
		# self.tools.find_one_and_replace({"_id":updated_tool['_id']}, updated_tool)