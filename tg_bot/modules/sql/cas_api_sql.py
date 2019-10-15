import threading

from sqlalchemy import Column, String, Boolean
from tg_bot.modules.sql import BASE, SESSION

class CombotCASStatus(BASE):
    __tablename__ = "cas_stats"
    chat_id = Column(String(14), primary_key=True)
    status = Column(Boolean, default=True)
    
    def __init__(self, chat_id, status):
        self.chat_id = str(chat_id) #chat_id is int, make sure it's string
        self.status = status

CAS_LOCK = threading.RLock()

def get_status(chat_id):
    try:
        resultObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if resultObj:
            return resultObj.status
        return False
    finally:
        SESSION.close()

def set_status(chat_id, status):
    with CAS_LOCK:
        prevObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if prevObj:
            SESSION.delete(prevObj)
        newObj = CombotCASStatus(str(chat_id), status)
        SESSION.add(newObj)
        SESSION.commit()
