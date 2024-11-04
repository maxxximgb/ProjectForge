import flask
from threading import Thread

from flask import request


def run_flask():
    return
    app = flask.Flask("ChatListenner")
    flask_thread = Thread(target=app.run())
    flask_thread.start()


    @app.route('/sendmessage', methods=['POST'])
    def receive_message():
        message = request.json
        #TODO система сообщений