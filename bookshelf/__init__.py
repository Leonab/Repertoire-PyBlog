import json
import logging

from flask import current_app, Flask, redirect, request, session, url_for
#from google.cloud import error_reporting
import httplib2
from oauth2client.contrib.flask_util import UserOAuth2


oauth2 = UserOAuth2()


def create_app(config, debug=False, testing=False, config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(config)

    app.debug = debug
    app.testing = testing

    if config_overrides:
        app.config.update(config_overrides)

    # Setup the data model.
    with app.app_context():
        model = get_model()
        model.init_app(app)

    # Initalize the OAuth2 helper.
    oauth2.init_app(
        app,
        scopes=['email', 'profile'],
        authorize_callback=_request_user_info)

    # Add a logout handler.
    @app.route('/logout')
    def logout():
        # Delete the user's profile and the credentials stored by oauth2.
        del session['profile']
        session.modified = True
        oauth2.storage.delete()
        return redirect(request.referrer or '/')

    # Register the Bookshelf CRUD blueprint.
    from .crud import crud
    app.register_blueprint(crud, url_prefix='/posts')

    # Add a default root route.
    @app.route("/")
    def index():
        return redirect(url_for('crud.list'))

    # Add an error handler that reports exceptions to Stackdriver Error
    # Reporting. Note that this error handler is only used when debug
    # is False
    # [START setup_error_reporting]
    @app.errorhandler(500)
    def server_error(e):
        client = error_reporting.Client(app.config['PROJECT_ID'])
        client.report_exception(
            http_context=error_reporting.build_flask_context(request))
        return """
        An internal error occurred.
        """, 500
    # [END setup_error_reporting]

    return app


def get_model():
    model_backend = current_app.config['DATA_BACKEND']
    if model_backend == 'mongodb':
        from . import model_mongodb
        model = model_mongodb
    else:
        raise ValueError(
            "No appropriate databackend configured. "
            "Please specify mongodb")

    return model


def _request_user_info(credentials):
    http = httplib2.Http()
    credentials.authorize(http)
    resp, content = http.request(
        'https://www.googleapis.com/plus/v1/people/me')

    print("response----",content)

    if resp.status != 200:
        current_app.logger.error(
            "Error while obtaining user profile: %s" % resp)
        return None

    session['profile'] = json.loads(content.decode('utf-8'))
