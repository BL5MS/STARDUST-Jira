import os
from slackclient import SlackClient

OAUTH_TOKEN = os.environ.get("OAUTH_TOKEN")
VERI_TOKEN = os.environ.get("VERI_TOKEN")
BL5Channel = "U3CLHL00K"


class BarryBot(object):
    def __init__(self):
        self.name = "barry-bot"
        self.client = SlackClient(OAUTH_TOKEN)
        self.verification = VERI_TOKEN
        # Do some stuff with this in future to fetch bot ID:
        # Why can't I fetch bot ID by using the Oauthtoken?
        # self.oauth = {"client_id": os.environ.get("CLIENT_ID"),
        #       "client_secret": os.environ.get("CLIENT_SECRET"),
        #       # Scopes provide and limit permissions to what our app
        #       # can access. It's important to use the most restricted
        #       # scope that your app will need.
        #       "scope": "bot"}

    def send_message(self, text, channel=BL5Channel):
        print("Sending message, {} in channel {}".format(text, channel))
        print(self.client.api_call("chat.postMessage",
              text=text,
              channel=channel))

barryBot = BarryBot()
