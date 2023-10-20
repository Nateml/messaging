from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import os

# Load environment variables
db_password = os.getenv("DB_PASSWORD");

if db_password is None:
    raise Exception("Failed to connect to the database. The environment variable DB_PASSWORD is not set.")

# Create the Flask app
app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://root:{db_password}@localhost:3306/MysticQuest'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def hello_world():
    return 'Hello, World! :)'

@app.route('/users')
def getUsers():
    """
    Returns a JSON object containing a list of all users in the database.
    Each user is represented as a dictionary with a 'username' key.
    """
    users = Player.query.all()
    result = [{"username":user.username} for user in users]
    return jsonify(result)

@app.route('/msg', methods=['POST'])
def send_message():
    """
    Sends a message to a chat.

    Returns:
    - If successful, returns a JSON object with a success message and the ID of the new message.
    - If unsuccessful, returns a JSON object with an error message and a 400 status code.

    Parameters:
    - chatID (int): The ID of the chat to send the message to.
    - sender (str): The username of the player sending the message.
    - message (str): The message to send.

    Raises:
    - None
    """
    
    data = request.get_json()

    chatID = data['chatID']
    sender = data['sender']
    message = data['message']

    if (len(message)>1024):
        return jsonify({"message": "Message too long. Must be less than 1024 characters."}, 400)

    # make sure sender is in the chat
    chat = Chat.query.filter_by(id=chatID).first()
    if chat is None:
        return jsonify({"message": "Chat not found."}, 400)
    
    player = Player.query.filter_by(username=sender).first()
    if player is None:
        return jsonify({"message": "Sender not found."}, 400)

    if player not in chat.players:
        return jsonify({"message": "Sender not in chat."}, 400)

    new_message = Message(chatID=chatID, sender=sender, message=message)
    db.session.add(new_message)
    db.session.commit()

    return jsonify({"message": "Message sent successfully.", "messageID": new_message.id})

@app.route('/chats/<string:username>')
def get_chats(username : str):
        """
        Returns a list of chats associated with the given username.
        
        Args:
        - username (str): The username of the player whose chats are to be retrieved.
        
        Returns:
        - A JSON object containing a list of dictionaries, where each dictionary represents a chat.
            Each dictionary contains the following keys:
                - chatID (int): The ID of the chat.
                - name (str): The name of the chat.
                - isGroup (bool): A boolean value indicating whether the chat is a group chat or not.
        """
         
        chats = Player.query.filter_by(username=username).first().chats
        result = [{"chatID":chat.id, "name":chat.name, "isGroup":chat.isGroup} for chat in chats]
        return jsonify(result)

@app.route('/newchat/<string:name>/<int:isGroup>')
def create_chat(name : str, isGroup : int):
    """
    Creates a new chat with the given name and group status.

    Args:
        name (str): The name of the chat.
        isGroup (int): The group status of the chat. Must be 1 or 0.

    Returns:
        A JSON response containing a message indicating whether the chat was created successfully and the ID of the new chat.
    """
    
    if isGroup != 0 and isGroup != 1:
        return jsonify({"message": "Invalid value for isGroup. Must be 1 or 0."}, 400)

    new_chat = Chat(name=name, isGroup=isGroup)
    db.session.add(new_chat)
    db.session.commit()

    return jsonify({"message": "Chat created successfully.", "chatID": new_chat.id})

@app.route('/addmember/<int:chatID>/<string:username>')
def add_member_to_chat(chatID : int, username : str):
    """
    Adds a player to a chat by their username and chat ID.

    Args:
        chatID (int): The ID of the chat to add the player to.
        username (str): The username of the player to add to the chat.

    Returns:
        A JSON response indicating whether the player was added to the chat successfully or not.
    """
    
    chat = Chat.query.filter_by(id=chatID).first()
    if chat is None:
        return jsonify({"message": "Chat not found."}, 400)

    player = Player.query.filter_by(username=username).first()
    if player is None:
        return jsonify({"message": "Player not found."}, 400)

    chat.players.append(player)
    db.session.commit()

    return jsonify({"message": "Player added to chat successfully."})

@app.route('/messages/<int:chatID>/<int:limit>')
def get_messages_from_chat(chatID : int, limit : int):
    """
    Returns a list of messages from a specific chat, limited by the given limit parameter.
    
    Args:
    chatID (int): The ID of the chat to retrieve messages from.
    limit (int): The maximum number of messages to retrieve.
    
    Returns:
    A JSON object containing a list of messages, each with a messageID, sender, message, and createdAt field.
    """
    messages = Chat.query.filter_by(id=chatID).first().messages
    result = [{"messageID":message.id, "sender":message.sender, "message":message.message, "createdAt":message.createdAt} for message in messages[:limit]]
    return jsonify(result)

@app.route('/messages/pretty/<int:chatID>/<int:limit>')
def get_pretty_messages_from_chat(chatID : int, limit : int):
    messages = Chat.query.filter_by(id=chatID).first().messages
    dp = ""
    for m in messages:
        dp += m.sender + ": " + m.message + "\n"
    return jsonify({"value" : dp})

@app.route('/unread/<string:username>')
def get_unread_messages(username : str):
    messages_in_chats = Message.query.filter(Message.chatID.in_([chat.id for chat in Player.query.filter_by(username=username).first().chats])).all()
    #read_messages = Player.query.filter_by(username=username).first().player_messages_0.order_by(Message.createdAt.desc()).all()
    result = [{"messageID":message.id, "sender":message.sender, "message":message.message, "createdAt":message.createdAt} for message in messages_in_chats]
    return jsonify(result)



# THE FOLLOWING CODE WAS GENERATED BY THE flask-sqlacodegen PACKAGE
# https://pypi.org/project/flask-sqlacodegen/

t_chatmembers = db.Table(
    'chatmembers',
    db.Column('chatID', db.ForeignKey('chats.id'), primary_key=True, nullable=False),
    db.Column('member', db.ForeignKey('players.username'), primary_key=True, nullable=False, index=True)
)

class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    isGroup = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    createdAt = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())

    players = db.relationship('Player', secondary='chatmembers', backref='chats')

class Message(db.Model):
    __tablename__ = 'messages'
    __table_args__ = (
        db.CheckConstraint('(length(`message`) <= 1024)'),
    )

    id = db.Column(db.Integer, primary_key=True)
    chatID = db.Column(db.ForeignKey('chats.id'), nullable=False, index=True)
    sender = db.Column(db.ForeignKey('players.username'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    createdAt = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())

    chat = db.relationship('Chat', primaryjoin='Message.chatID == Chat.id', backref='messages')
    player = db.relationship('Player', primaryjoin='Message.sender == Player.username', backref='player_messages')
    players = db.relationship('Player', secondary='messagesread', backref='player_messages_0')

t_messagesread = db.Table(
    'messagesread',
    db.Column('messageID', db.ForeignKey('messages.id'), primary_key=True, nullable=False),
    db.Column('readBy', db.ForeignKey('players.username'), primary_key=True, nullable=False, index=True)
)

class Player(db.Model):
    __tablename__ = 'players'

    username = db.Column(db.String(255), primary_key=True)
    firstName = db.Column(db.String(255), nullable=False)
    lastName = db.Column(db.String(255), nullable=False)
    emailAddress = db.Column(db.String(255), nullable=False, unique=True)
    dateOfBirth = db.Column(db.Date, nullable=False)
