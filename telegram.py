import asyncio
import os
import time 
from telebot.async_telebot import AsyncTeleBot
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import requests as r
import json
import threading
from time import sleep
import logging

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BOT_TOKEN = "6892079811:AAFjrOyRIHaRnMPxQbjZ30ePd4Ctq5_OKls"
msgs = []
bot = AsyncTeleBot(BOT_TOKEN)
os.environ['isActive'] = "False"
logging.basicConfig(level=logging.DEBUG)


async def syncmessages(uid, message):
        while os.environ['isActive'] == "True":
            try:
                res = r.get("https://api.emailx.es/v1/listemails?uid="+uid+"&n=1", timeout=60)
                if res.text != "[]":
                    msg = json.loads(res.text)[0]
                    if msg['subject'] not in msgs:
                        await bot.reply_to(message, f"📅 {msg['date']}\n🙍🏻‍♂️ {msg['sender']}\n📋 {msg['subject']}\n🤖 {msg['summary']}")
                        msgs.append(msg['subject'])
                        time.sleep(60)
                    else:
                        time.sleep(60)
                        pass
                else:
                    time.sleep(60)
                    pass
            except:
                pass
            
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "🤖 Este es el BOT de Emailx.ai, me encargaré de leer y resumir todos los mensajes que entren en tu INBOX\n➡️ Para conectar tu cuenta, escribe '/connect', un espacio y tu UID de usuario que encontrarás en la APP")

@bot.message_handler(commands=['connect'])
async def connect(message):
    os.environ['isActive'] = "True"
    uid = str(message.text.split()[1])
    rs = r.get("https://api.emailx.es/v1/oauth?uid="+uid)
    if 'credentials' in rs.text:
        await bot.reply_to(message, "🤖 BOT running and syncing with your mail account")
        await syncmessages(uid, message)
    else:
        await bot.reply_to(message, "🤖 The USER is not logged in our platform")
    
@bot.message_handler(commands=['stop'])
async def send_welcome(message):
    os.environ['isActive'] = "False"
    await bot.reply_to(message, "🤖 BOT stopped")

async def start():
    await bot.polling(none_stop=True)

if __name__== '__main__':
    try:
        asyncio.run(start())
    except Exception as e:
        print(e)
        pass
