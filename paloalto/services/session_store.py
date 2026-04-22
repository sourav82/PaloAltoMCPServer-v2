
# Replace with Redis in production

SESSION_DB = {}

def update_session(session_id: str, data: dict):
    if session_id not in SESSION_DB:
        SESSION_DB[session_id] = {}
    SESSION_DB[session_id].update(data)


def get_session(session_id: str):
    return SESSION_DB.get(session_id, {})
