import os
import time, datetime
import re
import json
import requests
from slackclient import SlackClient

TOKEN = 'xoxb-348528344930-0bPU7drO675BY16UNo42oX9K'
#TOKEN = os.environ.get('TOKEN')
slack_client = SlackClient(TOKEN)
bot_id = None

RTM_READ_DELAY = 1 # delay beetween reading

def parse_bot_msgs(slack_events):

    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id = event["user"]
            message = event["text"]
            return user_id, message, event["channel"]
    return None, None, None

def parse_direct_message(message_text):
    matches = re.search("^<@(|[WU].+?)>(.*)", message_text)
    return matches.group(2).strip() if matches else None

def write_data(data):
    with open('data.json', 'w') as outdata:
        json.dump(data, outdata, sort_keys=True, indent=4)

def read_data():
    with open('data.json', 'r') as indata:
        ret_data = json.load(indata)
    return ret_data

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):

        print("Start bot...")

        bot_id = slack_client.api_call("auth.test")["user_id"]

        print("bot_id {}".format(bot_id))

        while True:
            rtm_read = slack_client.rtm_read()

            user_id, msg, channel = parse_bot_msgs(rtm_read)
            if msg:
                message_data = (msg, str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

                params = dict(
                            token=TOKEN,
                            user=user_id
                        )

                profile = requests.get("https://slack.com/api/users.info", params).json()
                name = profile["user"]["name"]
                real_name = profile["user"]["real_name"]
                wdata = None
                try:
                    wdata = read_data()
                    if wdata == None:
                        raise Exception
                    try:
                        msgs = wdata.get(str(user_id)).get("messages")
                        msgs.append(message_data)
                    except:
                        msgs = [message_data]

                    dest = dict({str(user_id): {"_name": name, "_real_name": real_name, "messages": msgs} })
                    wdata.update(dest)
                    write_data(wdata)
                except Exception as e:
                    print(e)
                    wdata = {}
                    msgs = [message_data]
                    dest = dict({str(user_id): {"_name": name, "_real_name": real_name, "messages": msgs} })
                    wdata.update(dest)
                    write_data(wdata)

                command = parse_direct_message(msg)

                if command == "show_messages":
                    slack_client.api_call(
                        "chat.postMessage",
                        channel=channel,
                        text=str(wdata)
                    )

            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed!")