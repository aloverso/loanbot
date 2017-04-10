import time

'''
A class that deals with the messages we receive from users
'''
class ConversationHandler():
    '''
    create a new conversation handler with a given database client
    '''
    def __init__(self, database_client):
        self.database_client = database_client
        self.checkout_words = ['check out', 'checkout', 'checking out', 'take', 'took', 'taking', 'grabbing', 'grab', 'grabbed', 'checked out', 'borrow', 'borrowed']
        
        self.NO_CONTACT = 0
        self.SENT_GREETING = 1
        self.WANT_CHECKOUT = 2
        self.CONFIRM_TOOL = 4
        self.HOW_LONG = 5
        self.CLOSING = 6
    
    '''
    searches through a message looking for names of tools from the tools database
    returns a list of tool names found, empty if none found
    '''
    def find_tool_names_in_message(self, message):
        found_tools = []
        tools_list = self.database_client.get_all_tools()
        #loop through list looking for tool names in message
        for tool in tools_list:
            if tool['name'] in message:
                found_tools.append(tool)
        return found_tools

    '''
    creates a string of all tools a user is attempting to check out
    '''
    def make_tool_string(self, user):
        tool_string = ''
        print('temp_tools', user['temp_tools'])
        for tool in user['temp_tools']:
            tool_string = tool_string + tool['name'] + " and " # allow for a list of tools
        # remove final and from string
        tool_string = tool_string[:-5]
        print('tool string:', tool_string)
        return tool_string

    '''
    Parses the loan time quick reply message to store a due_date 
    for the tool/s the user wants to check out. uses import time
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
        #if the user is initiating contact
        if user['stage'] == self.NO_CONTACT:
            # check for checkout words
            if any(word in message for word in self.checkout_words):
                # id as checkout request
                user['stage'] = self.WANT_CHECKOUT
            else:
                # send greeting and ask what tool
                response = "Hi there! I'm the loan bot, what tool would you like to check out?"
                user['stage'] = self.SENT_GREETING
                return user, response, None

        #if the user wants to check out something
        if user['stage'] == self.WANT_CHECKOUT or user['stage'] == self.SENT_GREETING:
            tools_wanted = self.find_tool_names_in_message(message)
            user['temp_tools'] = tools_wanted
            
            #if we found a tool name/s in the message
            if len(tools_wanted) > 0:
                tool_string = self.make_tool_string(user)
                print('tool string in line:', tool_string)
                response = "Sounds like you want to check out a {}, is that correct?".format(tool_string)
                user['stage'] = self.CONFIRM_TOOL
                return user, response, ['yes','no']
            
            #if we could not identify a tool name/s in the message
            else:
                user['stage'] = self.WANT_CHECKOUT
                return user, "What tool do you want to check out?", None

        #we check that we parsed the correct tool/s...
        if user['stage'] == self.CONFIRM_TOOL:
            #...if so, we find out how long the loan will be
            if message == 'yes':
                response = "Great! Is a loan time of 1 day okay?"
                user['stage'] = self.HOW_LONG
                return user, response, ['yes', '12 hours instead', '3 days instead']

            #...if not, we try again
            else:
                user['temp_tools'] = []
                user['stage'] = self.WANT_CHECKOUT
                return user, "Sorry I misunderstood.  What tool do you want to check out?", None

        #update user and tool db based on the loan time
        if user['stage'] == self.HOW_LONG:
            tool_string = self.make_tool_string(user)
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

        print('I GOT TO THE END, OH NO')
        return user

        ## TODO: check for cancelling
