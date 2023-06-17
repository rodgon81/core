class SessionLoginCap:
    def __init__(self, session_id, challenge, iterations, is_irreversible, session_id_version, salt):
        self.session_id = session_id
        self.challenge = challenge
        self.iterations = iterations
        self.is_irreversible = is_irreversible
        self.session_id_version = session_id_version
        self.salt = salt
