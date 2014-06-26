import urllib
import http.client
import json

REDIRECT_URI = 'http://lvh.me:6543/oauth2_callback?service='
#REDIRECT_URI = 'http://fathomless-lowlands-8037.herokuapp.com/oauth2_callback?service='

SERVICE_GOOGLE_PLUS = 'google-plus'
SERVICE_GOOGLE_PLUS_CLIENT_ID = '369228793883-po5c6a8bmtjj3rpbu83jojp98111prj3.apps.googleusercontent.com'
SERVICE_GOOGLE_PLUS_SECRET = 'E3jOQ6IWsaUi0pfNBF6WyY8o'

SERVICE_GITHUB = 'github'
SERVICE_GITHUB_CLIENT_ID = '372294ce61fed7fea976'
SERVICE_GITHUB_SECRET = 'b77a8b8e873a7ced50b29988dd787cb9f912204f'

SERVICES = {
    SERVICE_GOOGLE_PLUS: {
        'auth': {
            'host': 'accounts.google.com',
            'path': '/o/oauth2/auth',
            'params': {
                #'state': 'shoud be filled later',
                'response_type': 'code',
                'client_id': SERVICE_GOOGLE_PLUS_CLIENT_ID,
                'redirect_uri': REDIRECT_URI + SERVICE_GOOGLE_PLUS,
                'scope': 'profile',
                'access_type': 'offline',
                'approval_prompt': 'force'
            }
        },
        'token': {
            'host': 'accounts.google.com',
            'port': 443,
            'path': '/o/oauth2/token',
            'params': {
                #'code': 'shoud be filled later',
                'client_id': SERVICE_GOOGLE_PLUS_CLIENT_ID,
                'client_secret': SERVICE_GOOGLE_PLUS_SECRET,
                'redirect_uri': REDIRECT_URI + SERVICE_GOOGLE_PLUS,
                'grant_type': 'authorization_code'
            }
        },
        'user': {
            'host': 'www.googleapis.com',
            'port': 443,
            'path': '/userinfo/v2/me',
            'params': {
                #'access_token': 'shoud be filled later'
            }
        }
    },
    SERVICE_GITHUB: {
        'auth': {
            'host': 'github.com',
            'path': '/login/oauth/authorize',
            'params': {
                #'state': 'shoud be filled later',
                'response_type': 'code',
                'client_id': SERVICE_GITHUB_CLIENT_ID,
                'redirect_uri': REDIRECT_URI + SERVICE_GITHUB,
                'scope': 'user',
            }
        },
        'token': {
            'host': 'github.com',
            'port': 443,
            'path': '/login/oauth/access_token',
            'params': {
                #'code': 'shoud be filled later',
                'client_id': SERVICE_GITHUB_CLIENT_ID,
                'client_secret': SERVICE_GITHUB_SECRET,
                'redirect_uri': REDIRECT_URI + SERVICE_GITHUB
            }
        },
        'user': {
            'host': 'api.github.com',
            'port': 443,
            'path': '/user',
            'params': {
                'access_token': 'shoud be filled later'
            }
        }
    }
}

def __https_request(host, port, method, path, body=None, headers=None):
    connection = http.client.HTTPSConnection(host, port)
    connection.set_debuglevel(1)
    connection.request(method, path, body=body, headers=headers)
    return connection.getresponse()

def __https_post_request(host, port, path, body=None):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*, application/json',
        'Accept-Charset': 'utf-8'
    }
    return __https_request(host, port, 'POST', path, body=body, headers=headers)

def __https_get_request(host, port, path):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': '*/*, application/json',
        'Accept-Charset': 'utf-8'
    }
    return __https_request(host, port, 'GET', path, headers=headers)

def is_service(service_id):
    return service_id in SERVICES

def get_auth_url(service_id, state):
    auth = SERVICES[service_id]['auth']
    params = auth['params']
    params['state'] = state
    params = urllib.parse.urlencode(params)
    return 'https://{}{}?{}'.format(auth['host'], auth['path'], params)

def exchange_code(service_id, code):
    token = SERVICES[service_id]['token']
    params = token['params']
    params['code'] = code
    params = urllib.parse.urlencode(params)
    response = __https_post_request(
        token['host'],
        token['port'],
        token['path'],
        body=params
    )
    content_type = response.getheader('Content-Type').lower()
    if (response.status == 200) and (content_type.find('application/json') != -1):
        buf = str(response.read(), 'utf-8')
        return json.loads(buf)
    return None

def get_user_info(service_id, access_token):
    user = SERVICES[service_id]['user']
    params = user['params']
    params['access_token'] = access_token
    params = urllib.parse.urlencode(params)
    response = __https_get_request(
        user['host'],
        user['port'],
        user['path'] + '?' + params
    )
    content_type = response.getheader('Content-Type').lower()
    if (response.status == 200) and (content_type.find('application/json') != -1):
        buf = str(response.read(), 'utf-8')
        return json.loads(buf)
    return None
