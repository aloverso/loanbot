import os
from pymongo import MongoClient
import requests
import xml.etree.ElementTree as ET

MONGO_URI = os.environ['mongo_uri']
#ACCESS_TOKEN = os.environ['tind_access_token']

client = MongoClient(MONGO_URI)
db = client.olinloanbot
tools = db.tindtools

class Tool:
    def __init__(self, name, collection, resource_link, olin_id, alternate_names, image_url):
        self.name = name
        self.current_user = None
        self.current_due_date = None
        self.collection = collection
        self.resource_link = resource_link
        self.olin_id = olin_id
        self.alternate_names = alternate_names
        self.image_url = image_url

def parse_xml():

    r = requests.get("https://olin.tind.io/search?ln=en&p=&f=&c=Tools&c=Media+Equipment&of=xm")

    root = ET.fromstring(r.text)

    for record in root:
        name = ''
        collection = ''
        resource_link = ''
        olin_id = ''
        alternate_names = []
        image_url = ''
        
        for field in record:

            # get record id
            if field.attrib['tag'] == '001':
                olin_id = field.text

            # get title
            if field.attrib['tag'] == '245':
                name = field[0].text.lower()
            
            # get references 
            if field.attrib['tag'] == '500':
                resource_link = field[0].text

            # get image url 
            if field.attrib['tag'] == '856':
                image_url = field[0].text

            # get type
            if field.attrib['tag'] == '980':
                if field[0].text != 'BIB':
                    collection = field[0].text

            # get alternate names
            if field.attrib['tag'] == '246':
                alternate_names.append(field[0].text.lower())

        if image_url != '':
            new_tool = Tool(name, collection, resource_link, olin_id, alternate_names, image_url)
            tools.insert_one(new_tool.__dict__)

def create_tools(tools_list):
    for tool in tools_list:
        tools.insert_one(tool.__dict__)

parse_xml()

#create_tools(tools_list)