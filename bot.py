import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call('auth.test')['user_id']

message_counts = {}
welcome_messages = {}
pets = {}

class WelcomeMessage:
    START_TEXT = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': (
                'Hello sticky nation. Welcome to TiNyTiTs! \n\n'
                '*Get started by completing the tasks.*'
            )
        }
    }

    DIVIDER = {'type':'divider'}

    def __init__(self, channel, user):
        self.channel =  channel
        self.user = user
        self.icon_emoji = ':biting_lip:'
        self.timestamp = ''
        self.completed = False

    def get_message(self):
        return{
            'ts': self.timestamp,
            'channel': self.channel,
            'username': 'your mom',
            'icon_emoji': self.icon_emoji,
            'blocks': [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]
        }
    
    def _get_reaction_task(self):
        checkmark = ':biting_lip:'
        if not self.completed:
            checkmark =':white_circle:'
        
        text = f'*react to this message* {checkmark}'

        return {'type': 'section', 'text':{'type': 'mrkdwn', 'text': text}}
    
def send_welcome_message(channel, user):
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    if channel not in welcome_messages:
        welcome_messages[channel] = {}
    welcome_messages[channel][user] = welcome
    
@slack_event_adapter.on('message')
def message(payLoad):
    event = payLoad.get('event',{})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if user_id != None and BOT_ID != user_id:
        if user_id in message_counts:
            message_counts[user_id]+=1
        else:
            message_counts[user_id]=1
        #client.chat_postMessage(channel=channel_id, text=text)

        if text.lower() == 'start':
            send_welcome_message(f'@{user_id}', user_id)

@slack_event_adapter.on('reaction_added')
def reaction(payLoad):
    event = payLoad.get('event',{})
    channel_id = event.get('item', {}).get('channel')
    user_id = event.get('user')

    if f'@{user_id}' not in welcome_messages:
        return 
    
    welcome = welcome_messages[f'@{user_id}'][user_id]
    welcome.completed = True
    welcome.channel = channel_id
    messgae = welcome.get_message()
    updated_message = client.chat_update(**welcome.get_message())
    welcome.timestamp = updated_message['ts']

@app.route('/message-count', methods=['POST'])
def message_count():
    data=request.form
    user_id= data.get('user_id')
    channel_id= data.get('channel_id')
    message_count=message_counts.get(user_id,0)
    client.chat_postMessage(channel=channel_id, text=f"got it young man. message count: {message_count}")
    return Response(), 200   

class Pet:
    def __init__(self, name, species, owner):
        self.name = name
        self.species = species
        self.owner = owner
        self.hp = 100
        self.attack = 10
        self.defense = 5
        self.xp = 0
        self.level = 1

    def level_up(self):
        self.level += 1
        self.hp += 20
        self.attack += 5
        self.defense += 3
        print(f"{self.name} leveled up to {self.level}!")

@slack_event_adapter.on('message')
def message(payLoad):
    event = payLoad.get('event',{})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if user_id and BOT_ID != user_id:
        if text.lower().startswith("!adopt"):
            pet_name = text.split(' ',1)[1] if len(text.split())>1 else "Fluffy"
            species = "Axolot1"

            pet = Pet(pet_name, species, user_id)
            pets[user_id] = pet
            response_text = (f"Yayy! You've adopted a pet ˗ˏˋ 𓅰ˎˊ˗ \n"
                             f"Name: {pet.name}\nSpecies: {pet.species}\n"
                             f"Stats: HP: {pet.hp} | ATK: {pet.attack} | DEF: {pet.defense}\n"
                             f"Take care of my lil boy please")
    client.chat_postMessage(channel=channel_id, text=response_text)

if __name__ == "__main__":
    app.run(debug=True)