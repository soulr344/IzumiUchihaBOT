import threading

from sqlalchemy import Column, String, Boolean
from tg_bot.modules.sql import BASE, SESSION

class CombotCASStatus(BASE):
    __tablename__ = "cas_stats"
    chat_id = Column(String(14), primary_key=True)
    status = Column(Boolean, default=True)
    autoban = Column(Boolean, default=False)
    
    def __init__(self, chat_id, status, autoban):
        self.chat_id = str(chat_id) #chat_id is int, make sure it's string
        self.status = status
        self.autoban = autoban

CAS_LOCK = threading.RLock()

def get_status(chat_id):
    try:
        resultObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if resultObj:
            return resultObj.status
        return True
    finally:
        SESSION.close()

def set_status(chat_id, status):
    with CAS_LOCK:
        ban = False
        prevObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if prevObj:
            ban = prevObj.autoban
            SESSION.delete(prevObj)
        newObj = CombotCASStatus(str(chat_id), status, ban)
        SESSION.add(newObj)
        SESSION.commit()

def get_autoban(chat_id):
    try:
        resultObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if resultObj and returnObj.autoban:
            return resultObj.autoban
        return False
    finally:
        SESSION.close()
        
def set_autoban(chat_id, autoban):
    with CAS_LOCK:
        status = True
        prevObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if prevObj:
            status = prevObj.status
            SESSION.delete(prevObj)
        newObj = CombotCASStatus(str(chat_id), status, autoban)
        SESSION.add(newObj)
        SESSION.commit()
