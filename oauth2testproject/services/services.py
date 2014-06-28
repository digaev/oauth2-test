import urllib
import http.client
import json


def _https_request(host, port, method, path, body=None, headers=None):
    connection = http.client.HTTPSConnection(host, port)
    connection.set_debuglevel(1)
    connection.request(method, path, body=body, headers=headers)
    return connection.getresponse()

def _https_post_request(host, port, path, body=None):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*, application/json',
        'Accept-Charset': 'utf-8'
    }
    return _https_request(host, port, 'POST', path, body=body, headers=headers)

def _https_get_request(host, port, path):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': '*/*, application/json',
        'Accept-Charset': 'utf-8'
    }
    return _https_request(host, port, 'GET', path, headers=headers)

def _read_response(response):
    content_type = response.getheader('Content-Type').lower()
    if (response.status == 200) and (content_type.find('application/json') != -1):
        buf = str(response.read(), 'utf-8')
        return json.loads(buf)
    return None

# Factory
class Services(object):
    REDIRECT_URI = 'http://lvh.me:6543/oauth2_callback?service='
    #REDIRECT_URI = 'http://fathomless-lowlands-8037.herokuapp.com/oauth2_callback?service='

    class _ServiceBase(object):
        def __init__(self, auth_host, api_host):
            self.__auth_host = auth_host
            self.__api_host = api_host

        @property
        def auth_host(self):
            return self.__auth_host

        @property
        def api_host(self):
            return self.__api_host

        def get_auth_url(self, state):
            return NotImplementedError

        def exchange_code(self, code):
            return NotImplementedError

        def api_get(self, path, params):
            response = _https_get_request(
                self.api_host,
                443,
                '%s?%s' % (path, urllib.parse.urlencode(params))
            )
            return _read_response(response)

    class GooglePlus(_ServiceBase):
        ID = 'google-plus'
        CLIENT_ID = '369228793883-po5c6a8bmtjj3rpbu83jojp98111prj3.apps.googleusercontent.com'
        CLIENT_SECRET = 'E3jOQ6IWsaUi0pfNBF6WyY8o'

        def __init__(self):
            super(Services.GooglePlus, self).__init__('accounts.google.com', 'www.googleapis.com')

        def get_auth_url(self, state):
            params = urllib.parse.urlencode({
                'state': state,
                'response_type': 'code',
                'client_id': self.CLIENT_ID,
                'redirect_uri': Services.REDIRECT_URI + self.ID,
                'scope': 'profile',
                'access_type': 'offline',
                'approval_prompt': 'force'
            })
            return 'https://%s/o/oauth2/auth?%s' % (self.auth_host, params)

        def exchange_code(self, code):
            params = urllib.parse.urlencode({
                'code': code,
                'client_id': self.CLIENT_ID,
                'client_secret': self.CLIENT_SECRET,
                'redirect_uri': Services.REDIRECT_URI + self.ID,
                'grant_type': 'authorization_code'
            })
            response = _https_post_request(
                self.auth_host,
                443,
                '/o/oauth2/token',
                body=params
            )
            return _read_response(response)

        def get_user_info(self, access_token):
            params = {'access_token': access_token}
            return self.api_get('/userinfo/v2/me', params)

    class Github(_ServiceBase):
        ID = 'github'
        CLIENT_ID = '372294ce61fed7fea976'
        CLIENT_SECRET = 'b77a8b8e873a7ced50b29988dd787cb9f912204f'

        def __init__(self):
            super(Services.Github, self).__init__('github.com', 'api.github.com')

        def get_auth_url(self, state):
            params = urllib.parse.urlencode({
                'state': state,
                'response_type': 'code',
                'client_id': self.CLIENT_ID,
                'redirect_uri': Services.REDIRECT_URI + self.ID,
                'scope': 'user',
            })
            return 'https://%s/login/oauth/authorize?%s' % (self.auth_host, params)

        def exchange_code(self, code):
            params = urllib.parse.urlencode({
                'code': code,
                'client_id': self.CLIENT_ID,
                'client_secret': self.CLIENT_SECRET,
                'redirect_uri': Services.REDIRECT_URI + self.ID,
            })
            response = _https_post_request(
                self.auth_host,
                443,
                '/login/oauth/access_token',
                body=params
            )
            return _read_response(response)

        def get_user_info(self, access_token):
            params = {'access_token': access_token}
            return self.api_get('/user', params)

    SERVICES = {
        GooglePlus.ID: GooglePlus,
        Github.ID: Github
    };

    def is_service(self, service_id):
        return service_id in self.SERVICES

    def create_service(self, service_id):
        return self.SERVICES[service_id]()

