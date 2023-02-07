
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
    app.add_url_rule('/nonce',  view_func=get_nonce, methods = ['GET'], defaults={'red' : red})
    app.add_url_rule('/register' , view_func=validate_sign,methods=['POST'], defaults={'red' : red})
    return


def get_nonce(red):
    logging.info("get_nonce")
    """try:
        if request.headers['X-API-KEY']!=API_KEY:
            return jsonify('Unauthorized'), 403
    except KeyError:
        return jsonify('Unauthorized'), 403"""

    nonce = str(uuid.uuid1())
    red.setex(request.headers['did'], 180, json.dumps({"nonce" : nonce})) 
    return jsonify({nonce:nonce}) 


    



async def validate_sign(red):
    logging.info("validate_sign")
    username=request.form["username"]
    nonce=json.loads(red.get(username).decode())['nonce']
    didAuth = request.form["didAuth"]    
    password=request.form["password"]
    result = json.loads(await didkit.verify_presentation(didAuth, nonce))
    if(not result["errors"]):
        stream = os.popen("""
        cd /etc/matrix-synapse/
        register_new_matrix_user -c homeserver.yaml -u """+username+""" -p """+password+""" --no-admin""")
        output = stream.read()
        return(jsonify(output),200)
    else:
        return jsonify(result["errors"]), 403

    


if __name__ == '__main__':
    logging.info("app init")
    
    init_app(app,red)

    


    app.run( host = "localhost", port= mode.port, debug =True)
""",ssl_context='adhoc'"""

