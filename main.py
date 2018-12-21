# -*- coding: utf-8 -*-
import json
from flask import Flask, request

from src.handlers import *
from src.util.get_config import config
from src.util.time_interval import set_interval, nine_time

app = Flask(__name__)


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_event['event_time'] < (datetime.now() - timedelta(seconds=1)).timestamp():
        return make_response("this message is before sent.", 200, {"X-Slack-No-Retry": 1})

    if config['slack_verification'] != slack_event.get("token"):
        message = "Invalid Slack verification token: {}".format(slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        slack_event = slack_event['event']

        # 유저가 말한 건지 확인
        if "user" in slack_event:
            ChatBotHandler().state_handler(slack_event)
            return make_response("event catch", 200, {"X-Slack-No-Retry": 1})
        else:
            return make_response("bot", 200, {"X-Slack-No-Retry": 1})

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    # 9시마다 브리핑
    set_interval(ChatBotHandler().briefing_handler, nine_time())

    app.run('0.0.0.0', port=5000, debug=True)
