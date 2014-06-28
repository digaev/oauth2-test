import datetime
import json

from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    UserSession
    )

from .services.services import Services

class Views(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return Response()

    @view_config(
            route_name='home',
            layout='app_layout',
            renderer='templates/home.pt'
            )
    def home_view(self):
        view_data = {
            'project': 'oauth2-test-project',
            'title': 'Home',
            'user_logged': False
        }

        # Looking for user's session
        if 'sid' in self.request.cookies:
            session = UserSession.find_by_sid(self.request.cookies['sid'])
        else:
            session = None

        # Session was not found or this is the first visit
        if session is None:
            session = UserSession()
            DBSession.add(session)
            self.request.response.set_cookie('sid', session.session_id)

        # Session found. Ok, check if user is logged in
        elif session.oauth2_created_at is not None:
            # oauth2 is still alive?
            if session.oauth2_expired_in is None:
                view_data['user_logged'] = True
            else:
                view_data['user_logged'] = session.oauth2_expired_in > datetime.datetime.utcnow()

            if view_data['user_logged']:
                # Seems like everything is fine, getting the name
                user_info = session.user_info_json()
                if session.service_id == Services.GooglePlus.ID:
                    view_data['user_name'] = user_info['given_name']
                elif session.service_id == Services.Github.ID:
                    view_data['user_name'] = user_info['login']

        if not view_data['user_logged']:
            view_data['socials'] = Services.SERVICES.keys()
        return view_data

# Sign out
    @view_config(
            route_name='signout'
            )
    def signout_view(self):
        if 'sid' in self.request.cookies:
            session = UserSession.find_by_sid(self.request.cookies['sid'])
        else:
            session = None

        if session is not None:
            self.request.response.delete_cookie(session.session_id)
            DBSession.delete(session)
            DBSession.flush()
        else:
            self.request.response.status_int = 400
        return self.request.response

# Here we should return authentication url
    @view_config(
            route_name='oauth2_auth',
            renderer='json'
            )
    def oauth2_auth_view(self):
        session = UserSession.find_by_sid(self.request.cookies['sid'])
        services = Services()
        if (session is not None) and\
                ('service' in self.request.params) and\
                (services.is_service(self.request.params['service'])):
            service = services.create_service(self.request.params['service'])
            url = service.get_auth_url(self.request.cookies['sid'])
            return {'url': url}
        else:
            self.request.response.status_int = 400

# OAuth2 callback function, let's dance
    @view_config(
            route_name='oauth2_callback'
            )
    def oauth2_callback_view(self):
        services = Services()
        if ('service' in self.request.params) and\
                ('state' in self.request.params) and\
                (services.is_service(self.request.params['service'])):
            session = UserSession.find_by_sid(self.request.params['state'])
            if session is not None:
                msg = {
                    'success': '<html><body><strong>You have successfully logged in!</strong><br /><a href="javascript:window.close();">Close this window</a></body></html>',
                    'cancel': '<html><body><strong>Authentication cancelled.</strong><br /><a href="javascript:window.close();">Close this window</a></body></html>',
                    'error': '<html><body><strong>Some error has occurred</strong><br /><a href="javascript:window.close();">Close this window</a></body></html>'
                }

                if 'error' in self.request.params:
                    self.request.response.text = msg['cancel']
                elif 'code' in self.request.params:
                    service = services.create_service(self.request.params['service'])
                    at = service.exchange_code(self.request.params['code'])
                    if (at is None) or not ('access_token' in at):
                        self.request.response.text = msg['error']
                    else:
                        session.oauth2_init(self.request.params['service'], json.dumps(at))

                        ui = service.get_user_info(at['access_token'])
                        if ui is None:
                            session.oauth2_clear()
                            self.request.response.text = msg['error']
                        else:
                            session.user_info = json.dumps(ui)
                            self.request.response.text = msg['success']

                            # g+
                            if 'expires_in' in at:
                                expired_in = session.oauth2_created_at.timestamp() + at['expires_in']
                                session.oauth2_expired_in = datetime.datetime.fromtimestamp(expired_in)
                else:
                    self.request.response.text = msg['error']
        else:
            self.request.response.status_int = 400
        return self.request.response


conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_oauth2-test-project_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

