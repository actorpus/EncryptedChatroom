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

    def _command_authenticate(self, data):
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
        if (data["emphasis"] is not None and self.account["emphasis"]) or data["emphasis"] is None:
            for connection in connections:  # forward message packet to all clients
                if connection is not self:
                    data["username"] = self.account["display"]
                    connection.communication.send(**data)  # formats the dictionary into kwargs
        else:
            self.communication.send(
                type=MESSAGE,
                emphasis="WARNING",
                content="Client not authorised to send emphasis messages."
            )

    def _update_profile_command(self, data):
        if "display" in data.keys():
            self.account["display"] = data["display"]
            accounts[self.account["name"]]["display"] = data["display"]

            lock.acquire()
            with open("users.json", "w") as file:
                json.dump(accounts, file)
            lock.release()

            self.communication.send(
                type=MESSAGE,
                emphasis="CONFIRMATION",
                content="Display name changed to '%s'" % self.account["display"]
            )

    def _command_request_data(self, data):
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

    def run(self):
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
