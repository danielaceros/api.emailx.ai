from flask import Blueprint, request

blueprint = Blueprint("summary", __name__)

@blueprint.route("/public/summary")
def getEmails(): 
    # Variable creds will store the user access token. 
    # If no valid token found, we will create one. 
    args = request.args.get("r")
    if args == None:
        args = 1    
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
    result = service.users().messages().list(maxResults=int(args), userId='me').execute() 

    # We can also pass maxResults to get any number of emails. Like this: 
    # result = service.users().messages().list(maxResults=200, userId='me').execute() 
    messages = result.get('messages') 

    # messages is a list of dictionaries where each dictionary contains a message id. 
    msgslist = []
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
                # Now, the data obtained is in lxml. So, we will parse 
                # it with BeautifulSoup library 

                cleantext = st.decode("utf-8").replace("\n"," ").strip()
                ct = cleantext.split()
                sub = ' '.join(ct[:200])
                openai.organization = os.getenv('ORG_KEY')
                openai.api_key = os.getenv('API_KEY')
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
                    msgslist.append(msgs)
                else:
                    pass
            else:
                pass
        except Exception as e: 
            logging.error(traceback.format_exc())
    try:
        return msgslist
    except Exception as e:
        logging.error(traceback.format_exc())
