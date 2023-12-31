from distutils import errors
from time import perf_counter
from flask import Flask, request, redirect
import flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow 
from google.auth.transport.requests import Request 
import pickle 
from firebase_admin import auth
import firebase_admin
from firebase_admin import credentials
import backoff
import re
import webbrowser    
import os.path 
import nest_asyncio
import base64 
import json
import requests_async as res
import openai
import logging
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from apiclient.discovery import build
import os.path
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
cred = credentials.Certificate("sdk.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.secret_key = '123'
CORS(app)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
urls = []

@app.route("/v1/test")
async def status():
    return "<p>🤖 Server Running...</p>"

@app.route("/v1/testgpt")
async def testgpt():
    openai.organization = os.getenv('ORG_KEY')
    openai.api_key = os.getenv('API_KEY')
    msg = [
            {"role":"user","content":f"saluda"},
            ]
    chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=msg
    )
    return chat.choices[0].message.content

@app.route("/v1/testuser")
async def testuser():
    uid = request.args.get('uid')
    if os.path.exists(uid+".json"):
        return "True"
    else:
        return "False"

@app.route("/v1/oauth2callback")
async def oauth2callback():
    if 'uid' in flask.session:
        uid = flask.session['uid']
    else:
        uid = request.args.get('uid')
    if 'state' in flask.session:
        state = flask.session['state']
    else:
        state = request.args.get('state')

    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", scopes=SCOPES, state=state)
    flow.redirect_uri = "https://api.emailx.es/v1/oauth2callback"
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    cr = credentials.to_json()
    with open(uid+".json", "w+") as c:
        c.write(cr)
    return redirect("https://app.emailx.es")
    

@app.route("/v1/oauth", methods=['GET', 'POST'])
async def main():
  uid = request.args.get("uid")
  creds = None
  try:
    user = auth.get_user(uid)
  except Exception as e:
      return e
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
      flow.redirect_uri = "https://api.emailx.es/v1/oauth2callback"
      authorization_url, state = flow.authorization_url(
          access_type="offline",
          prompt="consent"
      )
      flask.session['state'] = state
      flask.session['uid'] = uid
      return redirect(authorization_url)

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
            if rs:
                return rs
            elif not rs:
                return "None"
            else:
                return "None"
        else:
            pass
            return "None"

    except Exception:
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
                url = "https://mail.google.com/mail/#inbox/"+id
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
                    clean = re.compile('<.*?>')
                    cleantext = st.decode("utf-8")
                    clss = re.sub(clean, '', cleantext)
                    ct = clss.replace("\n"," ").strip().split()
                    sub = ' '.join(ct[:100])
                    reply = await summary(sub)
                    msgs = {
                    "labels":labels,
                    "sender":sender,
                    "date":date,
                    "subject":subject,
                    "snippet":snippet,
                    "summary":reply,
                    "url":url
                    }
                    return msgs
            except:
                pass

    except HttpError as error:
        print(f"An error occurred: {error}")

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_time=30)
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
