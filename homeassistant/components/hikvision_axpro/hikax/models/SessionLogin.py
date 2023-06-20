class SessionLogin:
    def __init__(self, username, encoded_password, session_id, session_id_version):
        self.userName = username
        self.password = encoded_password
        self.sessionID = session_id
        self.sessionIDVersion = session_id_version
