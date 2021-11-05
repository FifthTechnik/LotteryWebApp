import base64
from datetime import datetime
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
from cryptography.fernet import Fernet
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from app import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # User authentication information.
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    pinkey = db.Column(db.String(100), nullable=False)

    # User activity information
    registered_on = db.Column(db.DateTime, nullable=True)
    last_logged_in = db.Column(db.DateTime, nullable=True)
    current_logged_in = db.Column(db.DateTime, nullable=True)

    # User information
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='user')

    # crypto key for user's lottery draws
    drawkey = db.Column(db.BLOB)

    # last login details for security logs
    registered_on = db.Column(db.DateTime, nullable=False)
    last_logged_in = db.Column(db.DateTime, nullable=True)
    current_logged_in = db.Column(db.DateTime, nullable=True)

    # Define the relationship to Draw
    draws = db.relationship('Draw')

    def __init__(self, email, firstname, lastname, phone, password, pinkey, role):
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.phone = phone
        self.password = generate_password_hash(password)
        self.pinkey = pinkey
        self.drawkey = base64.urlsafe_b64encode(scrypt(password, str(get_random_bytes(32)), 32, N=2 ** 14, r=8, p=1))
        self.role = role
        self.registered_on = datetime.now()
        self.last_logged_in = None
        self.current_logged_in = None


class Draw(db.Model):
    __tablename__ = 'draws'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    draw = db.Column(db.String(100), nullable=False)
    played = db.Column(db.BOOLEAN, nullable=False, default=False)
    match = db.Column(db.BOOLEAN, nullable=False, default=False)
    win = db.Column(db.BOOLEAN, nullable=False)
    round = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, user_id, draw, win, round, drawkey):
        self.user_id = user_id
        self.draw = encrypt(draw, drawkey)
        self.played = False
        self.match = False
        self.win = win
        self.round = round

    def decrypt_draw(self, drawkey):
        self.user_id = self.user_id
        self.draw = decrypt(self.draw, drawkey)
        self.played = self.played
        self.match = self.match
        self.win = self.win
        self.round = self.round
        return self

    def encrypt_draw(self, drawkey):
        self.user_id = self.user_id
        self.draw = encrypt(self.draw, drawkey)
        self.played = self.played
        self.match = self.match
        self.win = self.win
        self.round = self.round
        return self


# functions used for encrypting and decrypting lottery draws
def encrypt(data, drawkey):
    return Fernet(drawkey).encrypt(bytes(data, 'utf-8'))


def decrypt(data, drawkey):
    return Fernet(drawkey).decrypt(data).decode("utf-8")


# resets database and adds admin user
def init_db():
    db.drop_all()
    db.create_all()
    admin = User(email='admin@email.com',
                 password='Admin1!',
                 pinkey='BFB5S34STBLZCOB22K6PPYDCMZMH46OJ',
                 firstname='Alice',
                 lastname='Jones',
                 phone='0191-123-4567',
                 role='admin')

    db.session.add(admin)
    db.session.commit()


