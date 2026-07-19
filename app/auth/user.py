from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_id, email, role_name, full_name):
        self.id = str(user_id)
        self.email = email
        self.role = role_name
        self.full_name = full_name

    def get_id(self):
        return self.id
