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
        checkmark = ':white_check_mark:'
        if not self.completed:
            checkmark =':biting_lip:'
        
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

@app.route('/message-count', methods=['POST'])
def message_count():
    data=request.form
    user_id= data.get('user_id')
    channel_id= data.get('channel_id')
    message_count=message_counts.get(user_id,0)
    client.chat_postMessage(channel=channel_id, text=f"got it young man. message count: {message_count}")
    return Response(), 200   

if __name__ == "__main__":
    app.run(debug=True)