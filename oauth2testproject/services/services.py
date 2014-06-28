import urllib
import http.client
import json


def https_request(host, port, method, path, body=None, headers=None):
    connection = http.client.HTTPSConnection(host, port)
    connection.set_debuglevel(1)
    connection.request(method, path, body=body, headers=headers)
    return connection.getresponse()

def https_post_request(host, port, path, body=None):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*, application/json',
        'Accept-Charset': 'utf-8'
    }
    return https_request(host, port, 'POST', path, body=body, headers=headers)

def https_get_request(host, port, path):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': '*/*, application/json',
        'Accept-Charset': 'utf-8'
    }
    return https_request(host, port, 'GET', path, headers=headers)

def read_response(response):
    content_type = response.getheader('Content-Type').lower()
    if (response.status == 200) and (content_type.find('application/json') != -1):
        buf = str(response.read(), 'utf-8')
        return json.loads(buf)
    return None

# Factory
class Services(object):
    REDIRECT_URI = 'http://lvh.me:6543/oauth2_callback?service='
    #REDIRECT_URI = 'http://fathomless-lowlands-8037.herokuapp.com/oauth2_callback?service='

    class GooglePlus(object):
        ID = 'google-plus'
        CLIENT_ID = '369228793883-po5c6a8bmtjj3rpbu83jojp98111prj3.apps.googleusercontent.com'
        CLIENT_SECRET = 'E3jOQ6IWsaUi0pfNBF6WyY8o'

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
            return 'https://accounts.google.com/o/oauth2/auth?' + params

        def exchange_code(self, code):
            params = urllib.parse.urlencode({
                'code': code,
                'client_id': self.CLIENT_ID,
                'client_secret': self.CLIENT_SECRET,
                'redirect_uri': Services.REDIRECT_URI + self.ID,
                'grant_type': 'authorization_code'
            })
            response = https_post_request(
                'accounts.google.com',
                443,
                '/o/oauth2/token',
                body=params
            )
            return read_response(response)

        def get_user_info(self, access_token):
            params = urllib.parse.urlencode({
                'access_token': access_token
            })
            response = https_get_request(
                'www.googleapis.com',
                443,
                '/userinfo/v2/me?' + params
            )
            return read_response(response)

    class Github(object):
        ID = 'github'

        def get_auth_url(self, state):
            urllib.parse.urlencode({
                'state': state,
                'response_type': 'code',
                'client_id': self.CLIENT_ID,
                'redirect_uri': Services.REDIRECT_URI + self.ID,
                'scope': 'user',
            })
            return 'https://github.com/login/oauth/authorize?' + params

        def exchange_code(self, code):
            params = urllib.parse.urlencode({
                'code': code,
                'client_id': self.CLIENT_ID,
                'client_secret': self.CLIENT_SECRET,
                'redirect_uri': Services.REDIRECT_URI + self.ID,
            })
            response = https_post_request(
                'github.com',
                443,
                '/login/oauth/access_token',
                body=params
            )
            return read_response(response)

        def get_user_info(self, access_token):
            params = urllib.parse.urlencode({
                'access_token': access_token
            })
            response = https_get_request(
                'api.github.com',
                443,
                '/user?' + params
            )
            return read_response(response)

    SERVICES = {
        GooglePlus.ID: GooglePlus,
        Github.ID: Github
    };

    def is_service(self, service_id):
        return service_id in self.SERVICES

    def create_service(self, service_id):
        return self.SERVICES[service_id]()

