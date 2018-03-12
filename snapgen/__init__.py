# -*- coding: utf-8 -*-

from .config_private import smtp,privatekey

import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

# FIFO
fifo  = []

from flask import Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
import os.path
app_path = '/'.join(os.path.abspath(__file__).split('/')[:-2])
import bmemcached
memcache = bmemcached.Client(('127.0.0.1:11211',))

app.secret_key = privatekey

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

@app.route('/testerror')
def testerror():
    1/0

if 1: #enable_logging
    import logging
    from io import StringIO
    from logging.handlers import SMTPHandler
    from logging import StreamHandler,Formatter
    import os
    import inspect
    # os.path.realpath(__file__)

    class eaiHandler(StreamHandler):
        def emit(self,record):
            StreamHandler.emit(self,record)

    class eaiSMTPHandler(SMTPHandler):
        def getSubject(self,record):
            return "Erreur Snapgen: %s (%s)" % (record.message,str(record.exc_info[:-1][1]))

    class eaiContextFilter(logging.Filter):
        def filter(self,record):
            #record.user = session['id']['username'] if 'id' in session else ''
            record.context = str(inspect.trace()[-1][0].f_locals)
            return True

    eai_handler = eaiHandler(StringIO())
    mail_handler = eaiSMTPHandler((smtp['host'],smtp['port']),
                               'api@snapgen.orvdev.fr',
                               'observatoireapi@yahoo.com', 'Erreur Snapgen',credentials=(smtp['username'],smtp['password']),secure=(None,None))

    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Context:

%(context)s

Message:

%(message)s
'''))
    app.logger.addFilter(eaiContextFilter())
    app.logger.addHandler(mail_handler)
    app.logger.addHandler(eai_handler)

from .views import api
