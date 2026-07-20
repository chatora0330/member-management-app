from flask_login import UserMixin

# --- User クラス ---
class User(UserMixin):
    def __init__(self, id, name, password):
        self.id = id
        self.name = name
        self.password = password
        
                
    @classmethod
    def from_row(cls, row):
        return cls(row["id"], row["name"], row["password"])

