import socket
import threading
import random
import json
import pickle
import hashlib
from typing import *

encrypt = lambda a, b: b''.join([((x[0] + x[1]) % 255).to_bytes(1, "big") for x in zip(a, b)])
decrypt = lambda a, b: b''.join([((x[0] - x[1]) % 255).to_bytes(1, "big") for x in zip(a, b)])
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


with open("users.json", "r") as f:
    accounts: dict = json.load(f)


class Connection(threading.Thread):
    def __init__(self, addresses):
        super().__init__()
        self.sock: socket.socket = addresses[0]
        self.address: tuple[str, int] = addresses[1]

        self.running = True
        self.active_packets = {}
        self.authenticated = None

        self.account = {}

        lock.acquire()
        connections.append(self)
        lock.release()

    def send(self, **kwargs):
        data = pickle.dumps(kwargs)

        packet_key = random.randbytes(len(data))
        packet_id = random.randbytes(2)
        packet_state = b'\x03'

        data = packet_state + packet_id + encrypt(data, packet_key)

        self.active_packets[packet_id] = packet_key

        self.sock.send(data)

    def recv(self, bufsize) -> Union[None, dict]:
        data = self.sock.recv(bufsize)

        packet_state = data[0]
        packet_id = data[1:3]
        data = data[3:]

        if packet_state == 0:
            packet_key = random.randbytes(len(data))

            data = encrypt(data, packet_key)

            self.active_packets[packet_id] = packet_key

            data = b'\x01' + packet_id + data

            self.sock.send(data)

        elif packet_state == 2:
            packet_key = self.active_packets[packet_id]

            data = decrypt(data, packet_key)

            del self.active_packets[packet_id]

            ret: dict = pickle.loads(data)

            return ret

        elif packet_state == 4:
            packet_key = self.active_packets[packet_id]

            data = decrypt(data, packet_key)

            data = b'\x05' + packet_id + data

            del self.active_packets[packet_id]

            self.sock.send(data)

    def _command_authenticate(self, data):
        if data["username"] in accounts.keys() and sha_hash(data["password"]) == accounts[data["username"]]["password"]:
            self.authenticated = True
            self.account: dict = accounts[data["username"]]
            self.account["name"] = data["username"]

            self.send(type=AUTHENTICATION_CONFIRMATION)
        else:
            self.send(
                type=MESSAGE,
                emphasis="WARNING",
                content="Client authentication failed"
            )
            self.send(type=DESIST_FROM_EXISTENCE)

    def _command_message(self, data):
        if (data["emphasis"] is not None and self.account["emphasis"]) or data["emphasis"] is None:
            for connection in connections:  # forward message packet to all clients
                if connection is not self:
                    data["username"] = self.account["display"]
                    connection.send(**data)  # formats the dictionary into kwargs
        else:
            self.send(
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

            self.send(
                type=MESSAGE,
                emphasis="CONFIRMATION",
                content="Display name changed to '%s'" % self.account["display"]
            )

    def handle_data(self, data):
        command = data["type"]
        if command == AUTHENTICATE:
            self._command_authenticate(data)

        elif self.authenticated:
            if command == MESSAGE:
                self._command_message(data)

            elif command == UPDATE_PROFILE:
                self._update_profile_command(data)

            else:
                self.send(
                    type=MESSAGE,
                    emphasis="WARNING",
                    content="Invalid communication"
                )

        else:
            self.send(
                type=MESSAGE,
                emphasis="WARNING",
                content="Client not authenticated"
            )
            self.send(type=DESIST_FROM_EXISTENCE)

    def run(self):
        while self.running:
            try:
                data = self.recv(1024)

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
    con = sock.accept()
    Connection(con).start()
