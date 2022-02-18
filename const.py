HTTP_STATUS_CODE = {
    100: "Continue",
    200: "OK",
    202: "Non-Authoritative Information",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",  
    404: "Not Found",
    407: "Proxy Authentication Required",  
    408: "Request Timeout",  
    500: "Internal Server Error",  
    502: "Bad Gateway",  
    403: "Forbidden",  
    403: "Forbidden",  
    504: "Gateway Timeout",
    1000: "Message not set."
    }

MQTT_STATUS_CODE = {
    0: "Connection successful",
    1: "Connection refused – incorrect protocol version",
    2: "Connection refused – invalid client identifier",
    3: "Connection refused – server unavailable",
    4: "Connection refused – bad username or password",
    5: "Connection refused – not authorised",
    100: "Connection refused - other things"
    }

SECRETS = 'secrets.ini'

COOKIE_UID = "'uid=fff9c382-389f-4a47-8dc9-c5486fc3d9f5"
COOKIE_EGG_SESS = "EGG_SESS=XHfAhiHWwU__OUVeKh0IiITBnmwA-IIXEzTCHgHgww6ZYYddOPntPSwVz4Gx7ISbfU0WrvzOLungThcL-9D2KxavrtyPk8Mr2YXLFzJwvM0usPvhzYdt2Y2S9Akt5sjP'"


BASE_URL = "https://global.hoymiles.com/platform/api/gateway/"
LOGIN_API = "iam/auth_login"