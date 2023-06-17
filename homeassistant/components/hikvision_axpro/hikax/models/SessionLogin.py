class SessionLogin:
    def __init__(self, username, encoded_password, session_id, session_id_version):
        self.username = username
        self.password = encoded_password
        self.session_id = session_id
        self.session_id_version = session_id_version
