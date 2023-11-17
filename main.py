from distutils import errors
from time import perf_counter
from flask import Flask, request, redirect
from flask_cors import CORS
import os
import traceback
from dotenv import load_dotenv
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow 
from google.auth.transport.requests import Request 
import pickle 
import webbrowser    
import os.path 
import nest_asyncio
import base64 
import json
import httplib2
import requests_async as res
import openai
import logging
import asyncio
import aiohttp
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from apiclient.discovery import build
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

webbrowser.register('chrome', None, webbrowser.BackgroundBrowser("/usr/bin/chromium"))
app = Flask(__name__)
CORS(app)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
urls = []
nest_asyncio.apply()

@app.route("/v1/test")
def status():
    return "<p>🤖 Server Running...</p>"

@app.route("/v1/oauth", methods=['GET', 'POST'])
async def main():
  uid = request.args.get("uid")
  creds = None
  if os.path.exists(uid+".json"):
    creds = Credentials.from_authorized_user_file(uid+".json", SCOPES)
    return {"user":uid, "credentials":uid+'.json'}
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
      return {"user":uid, "credentials":uid+'.json'}
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server()
      with open(uid+".json", "w") as token:
        token.write(creds.to_json())
      return {"user":uid, "credentials":uid+'.json'}

@app.route("/v1/listemails")
async def listEmails(): 
    try:
        uid = request.args.get("uid")
        n = request.args.get("n")
        creds = None
        if os.path.exists(uid+".json"):
            creds = Credentials.from_authorized_user_file(uid+".json", SCOPES)
            service = build("gmail", "v1", credentials=creds)
            results = service.users().messages().list(maxResults=n, userId="me").execute()
            msg = results.get("messages")
            rs = []
            for m in msg:
                r = await getEmail(uid, m['id'])
                if(r):
                    rs.append(r)
            return rs
        else:
            pass
            return "None"

    except HttpError as error:
        print(f"An error occurred: {error}")
        return "None"

@app.route("/v1/getemail")
async def getEmail(uidx, idx): 
    try:
        uid2 = request.args.get("uid")
        id2 = request.args.get("id")
        if(uid2 and id2 == None):
            uid = uidx
            id = idx
        else:
            uid = uid2
            id = id2
        creds = None
        if os.path.exists(uid+".json"):
            creds = Credentials.from_authorized_user_file(uid+".json", SCOPES)
            service = build("gmail", "v1", credentials=creds)
            txt = service.users().messages().get(userId='me', id=id).execute()
            try: 
                payload = txt['payload'] 
                snippet = txt['snippet']
                headers = payload['headers'] 
                labels = txt['labelIds']

                if 'UNREAD' in labels:
                    for d in headers: 
                        if d['name'] == 'Subject': 
                            subject = d['value'] 
                        if d['name'] == 'From': 
                            sender = d['value'] 
                        if d['name'] == 'Date': 
                            date = d['value'] 

                    st = b''
                    if payload.get('parts') != None:
                        parts = payload['parts'][0]
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
                    else:
                        data = payload['body']['data'].replace("-","+").replace("_","/") 
                        decoded_data = base64.b64decode(data) 
                        st = decoded_data + st
                    cleantext = st.decode("utf-8").replace("\n"," ").strip()
                    ct = cleantext.split()
                    sub = ' '.join(ct[:200])
                    reply = await summary(sub)
                    msgs = {
                    "labels":labels,
                    "sender":sender,
                    "date":date,
                    "subject":subject,
                    "snippet":snippet,
                    "summary":reply
                    }
                    return msgs
            except:
                pass

    except HttpError as error:
        print(f"An error occurred: {error}")

@app.route("/v1/summaryemail")
async def summary(sub):
    openai.organization = os.getenv('ORG_KEY')
    openai.api_key = os.getenv('API_KEY')
    msg = [
            {"role":"user","content":f"resume en una línea el contenido del siguiente email: {sub}"},
            ]
    chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=msg
    )
    return chat.choices[0].message.content

if __name__ == "__main__":
   app.run(host='0.0.0.0',port=5000)