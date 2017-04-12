#!flask/bin/python
import unittest

from server import app
import conversationHandler
import fakeDatabaseClient
import messengerClient
# messenger_client = messengerClient.MessengerClient()
database_client = fakeDatabaseClient.fakeDatabaseClient()
conversation_handler = conversationHandler.ConversationHandler(database_client)

class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_find_tool_names_in_message(self):
        test_message_1 = "I would like to borrow the drill and the screwdriver, please!"
        test_message_2 = "I want to take out a drill"
        test_message_3 = "I think it's cool that the library has tools"
        self.assertEqual(conversation_handler.find_tool_names_in_message(test_message_1), [{
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
}])
        self.assertEqual(len(conversation_handler.find_tool_names_in_message(test_message_2)),1)
        self.assertEqual(len(conversation_handler.find_tool_names_in_message(test_message_3)),0)


if __name__ == '__main__':
    unittest.main()