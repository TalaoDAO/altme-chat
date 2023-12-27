from flask import Flask, request, jsonify
import uuid
import json
import redis
import string
import os
import environment
import didkit
import logging
import asyncio
from nio import AsyncClient, MatrixRoom, RoomMessageText
import requests
import urllib.parse


client = AsyncClient("https://matrix.talao.co", "@support:matrix.talao.co")


logging.basicConfig(level=logging.INFO)

with open('keys.json') as mon_fichier:
    data = json.load(mon_fichier)

app = Flask(__name__)
app.secret_key = data.get('secret_key')
API_KEY = data.get('API_KEY')
PASSWORD_SUPPORT = data.get('PASSWORD_SUPPORT')

characters = string.digits

# init environnement variable
myenv = os.getenv('MYENV')
if not myenv:
    myenv = "achille"
mode = environment.currentMode(myenv)

red = redis.Redis(host='127.0.0.1', port=6379, db=0)


def init_app(app, red):
    app.add_url_rule('/matrix/nonce',  view_func=nonce,
                     methods=['GET'], defaults={'red': red})
    app.add_url_rule('/matrix/register', view_func=register,
                     methods=['POST'], defaults={'red': red})
    app.add_url_rule('/matrix/send_message',
                     view_func=send_message, methods=['POST'])
    return


def nonce(red):
    logging.info("/nonce")
    try:
        if request.headers['X-API-KEY'] != API_KEY:
            return jsonify('Unauthorized'), 403
    except KeyError:
        return jsonify('Unauthorized'), 403
    nonce = str(uuid.uuid1())
    logging.info("did " + request.args.get('did'))
    logging.info("nonce "+nonce)
    red.setex(request.args.get('did'), 180, json.dumps({"nonce": nonce}))
    return jsonify(nonce), 200


async def register(red):
    logging.info("/register")
    logging.info(request.get_json())
    try:
        username = request.get_json()["username"]
        nonce = json.loads(red.get(username).decode())['nonce']
        didAuth = request.get_json()["didAuth"]
        logging.info(didAuth)
        password = request.get_json()["password"]
        result = json.loads(
            await didkit.verify_presentation(didAuth, '{}')
        )
        logging.info('check didAuth = %s', result)
    except (KeyError, AttributeError, ValueError)as error:
        logging.error(error)
        return jsonify(str(error.__class__)), 403

    if nonce != json.loads(didAuth)['proof']['challenge']:
        logging.info('nonce does not match')

    # if(not result["errors"]):
    username = username.replace(":", "-")
    logging.info("u "+username+" p "+password)
    logging.info("register_new_matrix_user -c /etc/matrix-synapse/homeserver.yaml -u " +
                 username+" -p "+password+" --no-admin")
    stream = os.popen("""
    cd /etc/matrix-synapse/
    /usr/bin/register_new_matrix_user -c /etc/matrix-synapse/homeserver.yaml -u """+username+""" -p """+password+""" --no-admin
    """)
    output = stream.read()
    logging.info(output)
    return (jsonify(output), 200)
    # else:
    #    return jsonify(result["errors"]), 403


async def send_message():
    logging.info("/send_message")
    try:
        if request.headers['X-API-KEY'] != API_KEY:
            return jsonify('Unauthorized'), 403
    except KeyError:
        return jsonify('Unauthorized'), 403
    did = request.get_json().get("did")
    did = did.replace("/", "%2F")
    message = request.get_json().get("message")
    room = '#'+did+':matrix.talao.co'
    room = urllib.parse.quote(room, safe='')
    logging.info("requesting "+'https://matrix.talao.co/_matrix/client/r0/directory/room/'+room)
    response = requests.get(
        'https://matrix.talao.co/_matrix/client/r0/directory/room/'+room)
    room_id = response.json().get("room_id")
    await client.login(PASSWORD_SUPPORT)
    await client.room_send(
        room_id=room_id,
        message_type="m.room.message",
        content={"msgtype": "m.text", "body": message},
    )
    await client.close()
    return ("ok", 200)

if __name__ == '__main__':
    logging.info("app init")
    app.run(host="localhost", port=mode.port, debug=True)

init_app(app, red)
