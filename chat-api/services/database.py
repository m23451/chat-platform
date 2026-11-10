"""database.py: contains mock database to test api"""

# mock database to save users and messages as well as generate ids for messages and users
# also to get messages and users by id

from datetime import datetime

users = {}
messages = []

user_id_counter = 1
message_id_counter = 1

def save_message(username, text, client_id):
    global user_id_counter
    global message_id_counter

    # check if user exists, if not create a new user
    if username not in users:
        users[username] = {
            "id": user_id_counter,
            "username": username,
            "created_at": datetime.now().isoformat()
        }

        user_id_counter += 1

    user = users[username]

    #contains message id counter, username, text, client id and time message was created
    message = {
        "id": message_id_counter,
        "author": username,
        "text": text,
        "client_id": client_id,
        "created_at": datetime.now().isoformat()
    }

    messages.append(message)
    message_id_counter += 1

    return message

def get_messages(before_id=None, limit=50):

    result = messages.copy()

    if before_id is not None:
        result = [message for message in result if message["id"] < before_id]


# return the last 'limit' messages in reverse order (newest first)
    return list(reversed(result[-limit:]))  
