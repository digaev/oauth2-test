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

class ViewBase(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.response = self.request.response
        self.session = None

    def __call__(self):
        return Response()

    def create_session(self):
        self.session = UserSession()
        DBSession.add(self.session)
        self.response.set_cookie('sid', self.session.session_id)

    def find_session(self, sid=None):
        if sid is None and 'sid' in self.request.cookies:
            sid = self.request.cookies['sid']
        if sid is not None:
            self.session = UserSession.find_by_sid(sid)
        return self.session is not None

class SiteView(ViewBase):
    def __init__(self, context, request):
        super(SiteView, self).__init__(context, request)

        if not self.find_session():
            self.create_session()

        self.user_logged = self.session.oauth2_is_alive()
        self.view_data = {
            'project': 'oauth2-test-project',
            'user_logged': self.user_logged
        }

    @view_config(
            route_name='home',
            layout='app_layout',
            renderer='templates/home.pt'
            )
    def home(self):
        self.view_data['title'] = 'Home'
        if self.user_logged:
            ui = self.session.user_info_json()
            if self.session.service_id == Services.GooglePlus.ID:
                self.view_data['user_name'] = ui['given_name']
            elif self.session.service_id == Services.Github.ID:
                self.view_data['user_name'] = ui['login']
        else:
            self.view_data['socials'] = Services.SERVICES.keys()
        return self.view_data

    @view_config(
            route_name='signout'
            )
    def signout(self):
        if self.session is not None:
            self.response.delete_cookie(self.session.session_id)
            DBSession.delete(self.session)
            DBSession.flush()
        else:
            self.response.status_int = 400
        return self.response

class OAuth2View(ViewBase):
    MESSAGES = {
        'success': '<html><body><strong>You have successfully logged in!</strong><br /><a href="javascript:window.close();">Close this window</a></body></html>',
        'cancel': '<html><body><strong>Authentication cancelled.</strong><br /><a href="javascript:window.close();">Close this window</a></body></html>',
        'error': '<html><body><strong>Some error has occurred</strong><br /><a href="javascript:window.close();">Close this window</a></body></html>'
    }

    def __init__(self, context, request):
        super(OAuth2View, self).__init__(context, request)
        self.services = Services()

    # Here we should return authentication url
    @view_config(
            route_name='oauth2_auth',
            renderer='json'
            )
    def auth(self):
        if self.find_session() and\
                'service' in self.request.params and\
                self.services.is_service(self.request.params['service']):
            service = self.services.create_service(self.request.params['service'])
            url = service.get_auth_url(self.request.cookies['sid'])
            return {'url': url}
        else:
            self.response.status_int = 400

    # OAuth2 callback function, let's dance
    @view_config(
            route_name='oauth2_callback'
            )
    def callback(self):
        if 'service' in self.request.params and\
                'state' in self.request.params and\
                self.services.is_service(self.request.params['service']):
            if self.find_session(self.request.params['state']):
                if 'code' in self.request.params:
                    if self.init_user_session():
                        self.response.text = self.MESSAGES['success']
                    else:
                        self.response.text = self.MESSAGES['error']
                elif 'error' in self.request.params:
                    self.response.text = self.MESSAGES['cancel']
                else:
                    self.response.text = self.MESSAGES['error']
        else:
            self.response.status_int = 400
        return self.response

    def init_user_session(self):
        service = self.services.create_service(self.request.params['service'])
        at = service.exchange_code(self.request.params['code'])
        if at is not None and 'access_token' in at:
            ui = service.get_user_info(at['access_token'])
            if ui is not None:
                if 'expires_in' in at:
                    try:
                        expires_in = int(at['expires_in'])
                    except:
                        expires_in = UserSession.DEFAULT_LIFETIME
                else:
                    expires_in = UserSession.DEFAULT_LIFETIME

                now = datetime.datetime.utcnow()

                self.session.service_id = self.request.params['service']
                self.session.oauth2_created_at = now
                self.session.oauth2_expired_in = datetime.datetime.fromtimestamp(now.timestamp() + expires_in)
                self.session.oauth2_access_token = json.dumps(at)
                self.session.user_info = json.dumps(ui)
                return True
        return False


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

