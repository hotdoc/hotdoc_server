# coding=utf-8
# Created 2014 by Janusz Skonieczny
import logging
import os
import sys
from hotdoc.utils.utils import load_all_extensions

# Setup simple logging fast, load a more complete logging setup later on
# Log a message each time this module get loaded.
logging.basicConfig(format='%(asctime)s %(levelname)-7s %(module)s.%(funcName)s - %(message)s')
logging.getLogger().setLevel(logging.DEBUG)
logging.disable(logging.NOTSET)
logging.info('Loading %s, app version = %s', __name__, os.getenv('CURRENT_VERSION_ID'))


# Detect if running on development server or in production environment
# The simplest auto detection is to detect if appliaction is run from here
# production environment would use WSGI app
PRODUCTION = __name__ != "__main__"
DEBUG = not PRODUCTION

SRC_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_FOLDER = os.path.join(SRC_DIR, "templates")
STATIC_FOLDER = os.path.join(SRC_DIR, "static")

try:
    import flask_social_blueprint
except ImportError:
    # in case we run it from the repo, put that repo on path
    import sys
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(SRC_DIR)), "src"))

from flask import Flask
from flask.ext.cors import CORS

app = Flask(__name__, template_folder=TEMPLATE_FOLDER,
        static_folder=STATIC_FOLDER)
CORS(app)
#app.debug = DEBUG
#app.testing = DEBUG  # WARNING: this will disable login_manager decorators


# -------------------------------------------------------------
# Load settings from separate modules
# -------------------------------------------------------------

import website.settings
app.config.from_object(website.settings)

config = "website.settings_prd" if PRODUCTION else "website.settings_dev"
import importlib
try:
    cfg = importlib.import_module(config)
    logging.debug("Loaded %s" % config)
    app.config.from_object(cfg)
except ImportError:
    logging.warning("Local settings module not found: %s", config)


# -------------------------------------------------------------
# Custom add ons
# -------------------------------------------------------------

from website.database import db
db.init_app(app)

# Enable i18n and l10n
from flask_babel import Babel
babel = Babel(app)

# Authentication
import auth.models
auth.models.init_app(app)

import auth.views
app.register_blueprint(auth.views.app)

# Doc service
import doc_server.views
app.register_blueprint(doc_server.views.app)

# -------------------------------------------------------------
# Development server setup
# -------------------------------------------------------------

@app.route('/<path:path>')
def static_proxy(path):
    print "hello baby", path
    try:
        res = app.send_static_file(path)
        print 'wtf', res
    except Exception as e:
        print "exception", e
    return "lol"

if app.debug:
    from werkzeug.debug import DebuggedApplication
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

def setup_doc_server(args):
    logging.debug("PRODUCTION: %s" % PRODUCTION)
    logging.debug("app.debug: %s" % app.debug)
    logging.debug("app.testing: %s" % app.testing)

    # making your the server externally visible simplifies networking configuration
    # for local vagrant based development
    logging.warn("We're binding to all your ip addresses. Don't forget to map `dev.example.com` to one of them")
    logging.warn("For more information see http://bit.ly/1xKtf8j")

    # Setup our initial pages
    load_all_extensions()
    doc_server.views.do_format(args)

    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(host="0.0.0.0", port=5055)
    doc_server.views.doc_tool.finalize()
    pass


if __name__ == "__main__":
    # for convenience in setting up OAuth ids and secretes we use the example.com domain.
    # This should allow you to circumvent limits put on localhost/127.0.0.1 usage
    # Just map dev.example.com on 127.0.0.1 ip address.
    setup_doc_server(sys.argv[1:])
