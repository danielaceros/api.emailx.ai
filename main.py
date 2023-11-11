from flask import Flask, request
from flask_cors import CORS
import traceback
from dotenv import load_dotenv
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow 
from google.auth.transport.requests import Request 
import pickle 
import os.path 
import base64 
import json
import openai
import logging

from src.infrastructure.api.routes import health, summary

logging.basicConfig(level=logging.DEBUG)

# Define the SCOPES. If modifying it, delete the token.pickle file. 
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'] 

app = Flask(__name__)

CORS(app)

app.register_blueprint(health.blueprint)
app.register_blueprint(summary.blueprint)

if __name__ == "__main__":
    app.run()