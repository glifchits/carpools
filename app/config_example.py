class BaseConfig(object):
    url = "http://localhost:5000"
    app_id = "<facebook app id>"
    app_secret = "<facebook app secret>"
    email_login = 'some@email.com'
    email_pass = 'Y0ur_p455wurd'

class LocalConfig(BaseConfig):
    pass

class ProdConfig(BaseConfig):
    url = "http://www.sharecar.ca"

exported = LocalConfig()

class GCONFIG:
    client_id = '<google client id>'
    email = '<google email>'
    client_secret = '<google client secret>'
    redirect_uri = exported.url + "/oauth2callback"
    js_origins = exported.url
    api_key = '<google api key>'
