import socket
import threading
import json
import hashlib
from typing import *
import security

print(socket.gethostbyname(socket.gethostname()))

sha_hash = lambda data: hashlib.sha256(data.encode()).hexdigest()

IP = ""
PORT = 3952

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((IP, PORT))
sock.listen(4)

lock = threading.Lock()
connections = []

MESSAGE = 0
DESIST_FROM_EXISTENCE = 1
AUTHENTICATE = 2
AUTHENTICATION_CONFIRMATION = 3
UPDATE_PROFILE = 4
REQUEST_DATA = 5

ascii_art = {
    "thumbs_up": """
\n  _
 ( ((
  \\ =\\
 __\\_ `-\\
(____))(  \\----
(____)) _  
(____))
(____))____/----

""",
    "thumbs_down": """
\n  _______
(( ____   \\--
(( _____
((_____
((____   -----
      /  /
     (_(( 

""",
    "smile": """
\n     ..::''''::..
   .;''        ``;.
  ::    ::  ::    ::
 ::     ::  ::     ::
 ::     ::  ::     ::
  ::  :.      .:  ::
   `;..``::::''..;'
     ``::,,,,::''

"""
}

with open("users.json", "r") as f:
    accounts: dict = json.load(f)


class Connection(threading.Thread):
    def __init__(self, addresses):
        super().__init__()
        self.sock: socket.socket = addresses[0]
        self.address: Tuple[str, int] = addresses[1]

        self.running = True
        self.authenticated = None
        self.account = {}

        self.communication = security.Communication(self.sock)

        lock.acquire()
        connections.append(self)
        lock.release()

        self.start()

    def _command_authenticate(self, data) -> None:
        """
        Authenticates the user, if authenticated allows user to continue using the chatroom, otherwise terminates the
        unauthorised user.
        :param dictionary data: The data.
        :return: Returns a message back to the client, telling it what to do.
        """
        if data["username"] in accounts.keys() and sha_hash(data["password"]) == accounts[data["username"]]["password"]:
            self.authenticated = True
            self.account: dict = accounts[data["username"]]
            self.account["name"] = data["username"]

            self.communication.send(type=AUTHENTICATION_CONFIRMATION)
        else:
            self.communication.send(
                type=MESSAGE,
                emphasis="WARNING",
                content="Client authentication failed"
            )
            self.communication.send(type=DESIST_FROM_EXISTENCE)

    def _command_message(self, data):
        """
        Handles messages being passed back and forth between user.
        :param dictionary data: The data.
        :return:
        """
        if (data["emphasis"] is not None and self.account["emphasis"]) or data["emphasis"] is None:
            for connection in connections:  # forward message packet to all clients
                if connection is not self:
                    error = False
                    data["username"] = connection.account["display"]
                    if data["username"][1] == "[":
                        data["username"] = data["username"][5:-4]

                    if data["ascii_art"]:
                        data["content"] = data["content"].replace(":thumbs up:", ascii_art["thumbs_up"])
                        data["content"] = data["content"].replace(":thumbs down:", ascii_art["thumbs_down"])
                        data["content"] = data["content"].replace(":smile:", ascii_art["smile"])

                    if "@" in data["content"]:
                        string = data["content"]
                        string = string.split(" ")

                        for counter, word in enumerate(string):
                            try:
                                if word[0] == "@" and word[1:] == data["username"]:
                                    string[counter] = "\033[46m" + word[1:] + "\033[0m"
                            except IndexError:
                                self.communication.send(
                                    type=MESSAGE,
                                    emphasis="WARNING",
                                    content="An error occurred."
                                )
                                error = True

                        data["content"] = " ".join(string)

                    if error:
                        break

                    if not error:
                        data["username"] = self.account["display"]
                        connection.communication.send(**data)  # formats the dictionary into kwargs

        else:
            self.communication.send(
                type=MESSAGE,
                emphasis="WARNING",
                content="Client not authorised to send emphasis messages."
            )

    def _update_profile_command(self, data) -> None:
        """
        Handles a user updating their profile.
        :param dictionary data: The data
        :return: What their account has been changed to.
        """
        if "display" in data.keys():
            self.account["display"] = data["display"]
            accounts[self.account["name"]]["display"] = data["display"]

        elif "colour" in data.keys():
            display_name = accounts[self.account["name"]]["display"]
            if display_name[1] == "[":
                display_name = display_name[5:-4]

            accounts[self.account["name"]]["display"] = data["colour"] + display_name + "\033[0m"

        lock.acquire()
        with open("users.json", "w") as file:
            json.dump(accounts, file)
        lock.release()

        self.communication.send(
            type=MESSAGE,
            emphasis="CONFIRMATION",
            content="Display name changed to \033[0m'%s'" % self.account["display"]
        )

    def _command_request_data(self, data) -> None:
        """
        A command for requesting data.
        :param dictionary data: The data
        :return: None
        """
        if "display" in data.keys() and data["display"]:
            data["display"] = self.account["display"]

        self.communication.send(**data)

    def handle_data(self, data):
        command = data["type"]
        if command == AUTHENTICATE:
            self._command_authenticate(data)

        elif self.authenticated:
            if command == MESSAGE:
                self._command_message(data)

            elif command == UPDATE_PROFILE:
                self._update_profile_command(data)

            elif command == REQUEST_DATA:
                self._command_request_data(data)

            else:
                self.communication.send(
                    type=MESSAGE,
                    emphasis="WARNING",
                    content="Invalid communication"
                )

        else:
            self.communication.send(
                type=MESSAGE,
                emphasis="WARNING",
                content="Client not authenticated"
            )
            self.communication.send(type=DESIST_FROM_EXISTENCE)

    def run(self) -> None:
        """
        Runs the server.
        :return: Returns handled data.
        """
        while self.running:
            try:
                data = self.communication.recv(1024)

                if data is not None:
                    self.handle_data(data)

            except ConnectionResetError:
                if self.authenticated:
                    print("Lost connection from", self.account["display"])
                    break
                else:
                    print("Lost connection from unauthenticated user")
                    break

        lock.acquire()
        connections.remove(self)
        lock.release()


while True:
    Connection(sock.accept())
