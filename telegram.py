import os 
import telebot
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import requests as r

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BOT_TOKEN = "6892079811:AAFjrOyRIHaRnMPxQbjZ30ePd4Ctq5_OKls"

bot = telebot.TeleBot(BOT_TOKEN)

async def syncmessages(uid):
    r.get("https://api.emailx.es/v1/listemails?uid="+uid+"&n=1")
    print(r)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Este es el BOT de Emailx.ai, me encargaré de leer y resumir todos los mensajes que entren en tu INBOX\n➡️ Para conectar tu cuenta, escribe '/connect', un espacio y tu UID de usuario que encontrarás en la APP")
@bot.message_handler(commands=['connect'])
def connect(message):
    uid = message.text.split()[1:]
    creds = None
    r.get("https://api.emailx.es/v1/isuserouath?uid="+uid)
    if os.path.exists(uid+".json"):
        creds = Credentials.from_authorized_user_file(uid+".json", SCOPES)
        bot.reply_to(message, "🤖 BOT synced and running...")
        syncmessages(uid)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            bot.reply_to(message, "🤖 BOT synced and running...")
            syncmessages(uid)
    


bot.infinity_polling()