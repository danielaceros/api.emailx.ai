from flask import Flask
import os
import traceback
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow 
from google.auth.transport.requests import Request 
import pickle 
import os.path 
import base64 
import email 
from bs4 import BeautifulSoup 
import json
import openai
import pandas as pd
import logging
import re

logging.basicConfig(level=logging.DEBUG)

# Define the SCOPES. If modifying it, delete the token.pickle file. 
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'] 

app = Flask(__name__)

@app.route("/v1/getsummary")

def getEmails(): 
    # Variable creds will store the user access token. 
    # If no valid token found, we will create one. 
    creds = None

    # The file token.pickle contains the user access token. 
    # Check if it exists 
    if os.path.exists('token.pickle'): 

        # Read the token from the file and store it in the variable creds 
        with open('token.pickle', 'rb') as token: 
            creds = pickle.load(token) 

    # If credentials are not available or are invalid, ask the user to log in. 
    if not creds or not creds.valid: 
        if creds and creds.expired and creds.refresh_token: 
            creds.refresh(Request()) 
        else: 
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES) 
            creds = flow.run_local_server(port=0) 

        # Save the access token in token.pickle file for the next run 
        with open('token.pickle', 'wb') as token: 
            pickle.dump(creds, token) 

    # Connect to the Gmail API 
    service = build('gmail', 'v1', credentials=creds) 

    # request a list of all the messages 
    result = service.users().messages().list(maxResults=1, userId='me').execute() 

    # We can also pass maxResults to get any number of emails. Like this: 
    # result = service.users().messages().list(maxResults=200, userId='me').execute() 
    messages = result.get('messages') 

    # messages is a list of dictionaries where each dictionary contains a message id. 

    # iterate through all the messages 
    for msg in messages: 
        # Get the message from its id 
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()
        # Use try-except to avoid any Errors 
        try: 
            # Get value of 'payload' from dictionary 'txt' 
            payload = txt['payload'] 
            snippet = txt['snippet']
            headers = payload['headers'] 
            labels = txt['labelIds']

            if 'UNREAD' in labels:
                # Look for Subject and Sender Email in the headers 
                for d in headers: 
                    if d['name'] == 'Subject': 
                        subject = d['value'] 
                    if d['name'] == 'From': 
                        sender = d['value'] 
                    if d['name'] == 'Date': 
                        date = d['value'] 

                # The Body of the message is in Encrypted format. So, we have to decode it. 
                # Get the data and decode it with base 64 decoder. 
                parts = payload.get('parts')[0]
                st = b''
                if(parts['body']['size']) != 0:
                    data = parts['body']['data'].replace("-","+").replace("_","/") 
                    decoded_data = base64.b64decode(data) 
                    st = decoded_data + st
                else:
                    data = parts['parts']
                    for d in data:
                        for i in d['parts']:
                            data = i['body']['data'].replace("-","+").replace("_","/") 
                            decoded_data = base64.b64decode(data) 
                            st = decoded_data + st
                print(json.dumps(d, indent=4))

                # Now, the data obtained is in lxml. So, we will parse 
                # it with BeautifulSoup library 

                cleantext = st.decode("utf-8").replace("\n"," ").strip()
                ct = cleantext.split()
                sub = ' '.join(ct[:200])
                openai.organization = "org-sB447O8rt52Ojn3ybUPQezwJ"
                openai.api_key = "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"
                msg = [
                    {"role":"user","content":f"resume en una línea el contenido del siguiente email: {sub}"},
                    ]
                chat = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=msg
                )
                reply = chat.choices[0].message.content
                # Printing the subject, sender's email and message 
                msgs = {
                    "labels":labels,
                    "sender":sender,
                    "date":date,
                    "subject":subject,
                    "snippet":snippet,
                    "summary":reply
                }
                if msgs:    
                    return msgs
                else:
                    return ""
            else:
                pass
        except Exception as e: 
            logging.error(traceback.format_exc())


if __name__ == "__main__":
   app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 5000)))