import urllib.request as url
import json

VERSION = "1.0"
CAS_QUERY_URL = "https://combot.org/api/cas/check?user_id="

def get_user_data(user_id):
    with url.urlopen(CAS_QUERY_URL + str(user_id)) as userdata_raw:
        userdata = json.loads(userdata_raw.read().decode())
        return userdata

def isbanned(userdata):
    return userdata['ok']

def banchecker(user_id):
    return isbanned(get_user_data(user_id))

def vercheck() -> str:
    return str(VERSION)
