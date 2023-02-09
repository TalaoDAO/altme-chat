
from flask import Flask,render_template, request, jsonify, redirect,session, Response,send_file
import uuid 
import json
import redis
import string
import random
import os
import environment
from datetime import datetime, timedelta
import didkit
import logging
logging.basicConfig(level=logging.INFO)


app = Flask(__name__)
app.secret_key ="SECRET_KEY"
API_KEY="API_KEY"

characters = string.digits

#init environnement variable
myenv = os.getenv('MYENV')
if not myenv :
   myenv='thierry'

mode = environment.currentMode(myenv)

red= redis.Redis(host='127.0.0.1', port=6379, db=0)


def init_app(app,red) :
    app.add_url_rule('/matrix/nonce',  view_func=nonce, methods = ['GET'], defaults={'red' : red})
    app.add_url_rule('/matrix/register' , view_func=register,methods=['POST'], defaults={'red' : red})
    return


def nonce(red):
    logging.info("/nonce")
    try:
        if request.headers['X-API-KEY']!=API_KEY:
            return jsonify('Unauthorized'), 403
    except KeyError:
        return jsonify('Unauthorized'), 403
    nonce = str(uuid.uuid1())
    logging.info("did " +request.args.get('did'))
    logging.info("nonce "+nonce)
    red.setex(request.args.get('did'), 180, json.dumps({"nonce" : nonce})) 
    return jsonify(nonce),200 


async def register(red):
    logging.info("/register")

    logging.info(request.get_json())
    
    try:
        username=request.get_json()["username"]
        nonce=json.loads(red.get(username).decode())['nonce']
        didAuth =request.get_json()["didAuth"]
        password=request.get_json()["password"]
        result = json.loads(
            await didkit.verify_presentation(didAuth, json.dumps({"challenge":nonce}))
        )
    except (KeyError, AttributeError,ValueError)as error:
        logging.error(error)
        return jsonify(str(error.__class__)),403
    #if(not result["errors"]):
    logging.info("u "+username+" p "+password)
    logging.info("register_new_matrix_user -c /etc/matrix-synapse/homeserver.yaml -u "+username+" -p "+password+" --no-admin")
    stream = os.popen("""
    cd /etc/matrix-synapse/
    /usr/bin/register_new_matrix_user -c /etc/matrix-synapse/homeserver.yaml -u """+username+""" -p """+password+""" --no-admin
    """)
    output = stream.read()
    logging.info(output)
    return(jsonify(output),200)
    #else:
    #    return jsonify(result["errors"]), 403


if __name__ == '__main__':
    logging.info("app init")

    app.run( host = "localhost", port= mode.port, debug =True)
init_app(app,red)



