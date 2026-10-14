from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_id, email, role_name, full_name):
        """Initialize a Flask-Login user from a user tuple row.

        Stores the id as a string (as Flask-Login expects) plus email,
        role name, and display name. Constructed from get_user_by_* tuples
        of the form (user_id, email, role_name, full_name).

        Args:
            user_id: Primary key of user_accounts.
            email: User email address.
            role_name: Role string (Student, Faculty, Librarian, Admin).
            full_name: Display name for templates and audit text.

        Returns:
            None; initializes the User instance in place.
        """
        self.id = str(user_id)
        self.email = email
        self.role = role_name
        self.full_name = full_name

    def get_id(self):
        """Return the Flask-Login session identifier for this user.

        Flask-Login calls this to serialize the user into the session.
        Returns the string id set at construction so the user loader can
        reload the same account on subsequent requests.

        Args:
            self: The authenticated User instance.

        Returns:
            String user id used as the session key.
        """
        return self.id
