import time

import messengerClient

'''
A class that deals with the messages we receive from users
'''
class ConversationHandler():
    '''
    create a new conversation handler with a given database client
    '''
    def __init__(self, database_client):
        self.database_client = database_client
        self.checkout_words = ['check', 'checking', 'checked', 'check out', 'checkout', 'checking out', 'take', 'took', 'taking', 'grabbing', 'grab', 'grabbed', 'checked out', 'borrow', 'borrowed', 'want']
        self.return_words = ['return', 'returned','returning','brought', 'bring', 'bringing', 'dropping', 'dropped', 'took back', 'left', 'done', 'done with', 'finished']
        self.closing_words = ['thanks', 'thank', 'ok', 'bye', 'goodbye', 'good-bye', 'okay', 'cancel', 'stop', 'fuck', 'yay']
        self.available_words = ['available', 'there']
        self.help_words = ['how do i', 'help', 'manual', 'documentation', 'how to', 'trouble', 'confused']

        self.NO_CONTACT = 0
        self.SENT_GREETING = 1
        self.WANT_CHECKOUT = 2
        self.CONFIRM_TOOL = 4
        self.HOW_LONG = 5
        self.CLOSING = 6
        self.WANT_RETURN = 7
        self.CONFIRM_TOOL_RETURN = 8
        self.AVAILABILITY_QUESTION = 9
        self.SEND_LIST = 10
    
    '''
    searches through a message looking for names of tools from the tools database
    returns a list of tool names found, empty if none found
    '''
    def find_tools_in_message(self, message):
        found_tools = []
        tools_list = self.database_client.get_all_tools()
        #loop through list looking for tool names in message
        for tool in tools_list:
            if tool['name'] in message:
                found_tools.append(tool)
            else:
                for alt_name in tool['alternate_names']:
                    if alt_name in message:
                        found_tools.append(tool)
        return found_tools

    '''
    creates a string of all tools a user is attempting to check out
    '''
    def make_tool_string(self, tool_list):
        tool_string = ''
        print('temp_tools', tool_list)
        for tool in tool_list:
            tool_string = tool_string + tool['name'] + " and " # allow for a list of tools
        # remove final and from string
        tool_string = tool_string[:-5]
        print('tool string:', tool_string)
        return tool_string

    '''
    Parses the loan time quick reply message to store a due_date 
    for the tool/s the user wants to check out. uses import time
    TODO: handle the case when we somehow get a different message 
    than the quick reply options were expecting in a way other than 
    making the due date "0"
    '''
    def parse_due_date(self, message):
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

    '''
    Uses the user's stage to parse the message and determine how to reply

    takes the message text string and a user (in dictionary format)

    returns a tuple:
    updated_user, response_text, quickreply

    updated_user is the user dictionary, possibly changed or updated_user
    response_text is the bot's response message
    quickreply is a field indicating whether this should be a quickreply response
        it either has the None value (not a quickreply message)
        or a list of quickreply options
    '''
    def determine_response_for_user(self, message, user):
        print('determine_response_for_user')
        
        if any(word in message for word in self.closing_words):
            response = "Glad to help. Bye!"
            user['stage'] = self.NO_CONTACT
            return user, response, None

        if any(word in message for word in self.help_words):
            response = ''
            tool_help_wanted = self.find_tools_in_message(message)
            if len(tool_help_wanted) >0:
                resource_links = ''
                for tool in tool_help_wanted:
                    resource_links += ' ' + tool['resource_link']
                response ="I have some resources that might be helpful, here are some links:" + resource_links
            else:
                response ="I think you want help but I think a librarian would be more helpful, I've forwarded your question to them. They should reach out to you soon."
                #TODO: send email to librarian here
            return user, response, None

        # this needs to be located above the NO_CONTACT check
        if user['stage'] == self.SEND_LIST:
            user['stage'] = self.NO_CONTACT
            if message == 'view more':
                print('said view more')
                return user, "SEND_LIST 0", None # 0 is key in server.py means send all
            print('past view more')

        #if the user is initiating contact
        if user['stage'] == self.NO_CONTACT:

            # trying to return
            if any(word in message for word in self.return_words):
                user['stage'] = self.WANT_RETURN

            # checking availability status
            elif any(word in message for word in self.available_words):
                tools_wanted = self.find_tools_in_message(message)
                response_string = ''
                quickreply = None
                if len(tools_wanted) >0:
                    unavailable_tools = []
                    for tool in tools_wanted:
                        available_modifier = ''
                        if tool['current_user'] != None:
                            available_modifier = 'not '
                            unavailable_tools.append(tool)
                        response_string += 'the {} is {}available and '.format(tool['name'], available_modifier)
                    response_string = response_string[:-5]

                    if len(unavailable_tools) > 0:
                        question = 'Would you like me to ask the tool borrowers to return them?'
                        response_string = response_string + '. ' + question
                        user['temp_tools'] = unavailable_tools
                        user['stage'] = self.AVAILABILITY_QUESTION
                        quickreply = ['yes', 'no']
                else:
                    response_string = "SEND_LIST 4" #send 4
                    user['stage'] = self.SEND_LIST

                return user, response_string, quickreply

            # checking out
            elif any(word in message for word in self.checkout_words):
                user['stage'] = self.WANT_CHECKOUT

            else:
                # send greeting and ask what tool
                response = "Hi there! I'm the loan bot, what can I help you with?"
                # user['stage'] = self.SENT_GREETING
                return user, response, None

        # if the user has asked about availability and we're finding out if we should
        # send a reminder to the borrowers or not
        if user['stage'] == self.AVAILABILITY_QUESTION:
            if message == 'yes':
                for tool in user['temp_tools']:
                    borrower_id = tool['current_user']
                    borrower_sender_id = self.database_client.find_user('_id', borrower_id)['sender_id']

                    # this is not the best code structure
                    # because we have this weird situation where the user we want to send a message to
                    # is not the user who sent us a message
                    messenger_client = messengerClient.MessengerClient()
                    reminder = "Hey, someone was looking to borrow the {} that you have checked out. It'd be great if you could return it if you're almost done.".format(tool['name'])
                    messenger_client.send_message(borrower_sender_id, reminder, None)

                user['stage'] = self.NO_CONTACT
                user['temp_tools'] = []
                return user, "All set! Hopefully they'll be back soon.", None

            else:
                user['stage'] = self.NO_CONTACT
                user['temp_tools'] = []
                return user, "Very well. Is there something else I can help with?", None

        #if the user wants to check out something
        if user['stage'] == self.WANT_CHECKOUT or user['stage'] == self.SENT_GREETING:
            tools_wanted = self.find_tools_in_message(message)
            user['temp_tools'] = tools_wanted
            
            #if we found a tool name/s in the message
            if len(tools_wanted) > 0:
                tool_string = self.make_tool_string(user['temp_tools'])
                print('tool string in line:', tool_string)
                response = "Sounds like you want to check out a {}, is that correct?".format(tool_string)
                user['stage'] = self.CONFIRM_TOOL
                return user, response, ['yes','no']
            
            #if we could not identify a tool name/s in the message
            else:
                user['stage'] = self.NO_CONTACT
                return user, "What can I help you with?", None

        #we check that we parsed the correct tool/s...
        if user['stage'] == self.CONFIRM_TOOL:
            #...if so, we find out how long the loan will be
            if message == 'yes':

                available = True
                tools_out = []

                # check if those tools are in right now
                for tool in user['temp_tools']:
                    if tool['current_user'] != None:
                        available = False
                        tools_out.append(tool)

                if available:
                    response = "Great! Is a loan time of 1 day okay?"
                    user['stage'] = self.HOW_LONG
                    return user, response, ['yes', '12 hours instead', '3 days instead']

                else:
                    response = "Sorry, the following tools are not available right now: {}".format(self.make_tool_string(tools_out))
                    user['stage'] = self.NO_CONTACT
                    return user, response, None

            #...if not, we try again
            else:
                user['temp_tools'] = []
                user['stage'] = self.NO_CONTACT
                return user, "Sorry I misunderstood.  What do you want to do?", None

        #update user and tool db based on the loan time
        if user['stage'] == self.HOW_LONG:
            tool_string = self.make_tool_string(user['temp_tools'])
            for tool in user['temp_tools']:
                tool['current_user'] = user['_id']
                tool['current_due_date'] = self.parse_due_date(message)
                self.database_client.update_tool(tool)
                user['tools'].append(tool['_id'])

            # TODO: how to handle loan time if they are checking out more than one tool

            #finish the interaction and reset the conversation stage
            response = "You're all set!  I'll remind you to return the {} before it's due.".format(tool_string)
            user['temp_tools'] = []
            user['stage'] = self.NO_CONTACT
            return user, response, None

        if user['stage'] == self.CONFIRM_TOOL_RETURN:
            #...if so, we find out how long the loan will be
            if message == 'yes':
                tool_string = self.make_tool_string(user['temp_tools'])

                # TODO: tell them if they're trying to return something they don't have
                #update tool
                for tool in user['temp_tools']:
                    if tool['current_user'] == user['_id']:
                        tool['current_user'] = None
                        tool['current_due_date'] = None
                    self.database_client.update_tool(tool)

                    # update user tool list
                    for checked_out_tool_id in user['tools']:
                        if checked_out_tool_id == tool['_id']:
                            user['tools'].remove(checked_out_tool_id)

                user['temp_tools'] = []
                user['stage'] = self.NO_CONTACT
                return user, "You're all set!  I've marked the {} as returned.".format(tool_string), None

            #...if not, we try again
            else:
                user['temp_tools'] = []
                user['stage'] = self.WANT_RETURN
                return user, "Sorry I misunderstood.  What tool do you want to return?", None

        if user['stage'] == self.WANT_RETURN:
            tools_returning = self.find_tools_in_message(message)
            user['temp_tools'] = tools_returning

            #if we found a tool name/s in the message
            if len(tools_returning) > 0:
                tool_string = self.make_tool_string(user['temp_tools'])
                print('tool string in line:', tool_string)
                response = "Sounds like you want to return a {}, is that correct?".format(tool_string)
                user['stage'] = self.CONFIRM_TOOL_RETURN
                return user, response, ['yes','no']

            #if we could not identify a tool name/s in the message
            else:
                user['stage'] = self.WANT_RETURN
                return user, "What tool do you want to return?", None

        print('I GOT TO THE END, OH NO')
        return user

        ## TODO: check for cancelling
