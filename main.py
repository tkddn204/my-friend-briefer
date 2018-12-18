from slacker import Slacker
from requests.sessions import Session

from src.util.get_config import config

token = config['slack_token']

slack = Slacker(token)

# Send a message to #general channel
slack.chat.post_message('#general', 'Hello fellow slackers!')

# Get users list
response = slack.users.list()
users = response.body['members']

# Advanced: Use `request.Session` for connection pooling (reuse)
with Session() as session:
    slack = Slacker(token, session=session)
    slack.chat.post_message('#general', 'All these requests')
    slack.chat.post_message('#general', 'go through')
    slack.chat.post_message('#general', 'a single https connection')
