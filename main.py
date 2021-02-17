import os

from flask import Flask
from flask import jsonify
from flask import request
from sms77api.Sms77api import Sms77api

app = Flask(__name__)


@app.route('/', methods=['POST'])
def handle():
    return handle_agent(Sms77VoiceAgent, request)


def handle_agent(cls, req):
    """Helper that routes 'method calls' to a real agent object."""

    content = req.json
    method = content['method']
    params = content.get('params')

    if method == 'register':
        response = cls.register()
    elif method == 'check':
        response = cls(params).check()
    elif method == 'receive':
        response = cls(params).receive(params['message'])
    else:
        response = {}

    return jsonify(response)


class Sms77VoiceAgent:
    def __init__(self, params):
        """Set some convenience variables.
        Object is created from scratch on each method invocation"""
        self.credentials = params['credentials']
        self.options = params['options']
        self.memory = params['memory'] or {}

    # noinspection PyMethodParameters
    def register():
        """Register our metadata"""

        return {
            'result': {
                'default_options': {
                    'apiKey': '{% credential sms77_api_key %}',
                    'from': None,
                    'text': None,
                    'to': None,
                    'xml': False,
                },
                'description': 'Agent to issue Text2Speech calls via Sms77.io.',
                'display_name': 'Sms77 Voice Agent',
                'name': 'Sms77VoiceAgent',
            }
        }

    def check(self):
        """This is run on schedule. Do something useful."""
        messages = []

        if self.memory.get('last_message'):
            messages.append(self.memory['last_message'])

        memory = self.memory.copy()
        memory.pop('last_message', None)

        return {
            'result': {
                'errors': [],
                'logs': ['Check done'],
                'memory': memory,
                'messages': messages,
            }
        }

    def receive(self, message):
        """Process message and do something with it."""
        errors = []
        messages = []
        payload = message['payload']

        self.memory['last_message'] = payload

        api_key = payload.pop('apiKey', os.getenv('SMS77_API_KEY'))
        if api_key is None:
            errors.append('Missing API key')

        text = payload.pop('text', None)
        if text is None:
            errors.append('Missing text')

        to = payload.pop('to', None)
        if to is None:
            errors.append('Missing to')

        if 0 == len(errors):
            messages.append(Sms77api(api_key, 'active-workflow').voice(
                to, text,
                payload.pop('xml', False), payload.pop('from', None)))

        return {
            'result': {
                'errors': errors,
                'logs': ['New message received'],
                'memory': self.memory,
                'messages': messages,
            }
        }


if __name__ == '__main__':
    app.run()
