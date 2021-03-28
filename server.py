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

        self.account = ()

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

    def run(self):
        while self.running:
            try:
                data = self.recv(1024)

                try:
                    if data is not None:
                        if data["type"] == "authenticate":
                            if data["username"] in accounts.keys() and sha_hash(data["password"]) == accounts[data["username"]]["password"]:
                                self.authenticated = True
                                self.account = accounts[data["username"]]

                                self.send(type="authentication confirmation")
                            else:
                                self.send(
                                    type="message",
                                    emphasis="WARNING",
                                    content="Client authentication failed"
                                )
                                self.send(type="desist from existence")

                        elif data["type"] == "message":
                            if self.authenticated:
                                if (data["emphasis"] is not None and self.account["emphasis"]) or data["emphasis"] is None:
                                    for connection in connections:  # forward message packet to all clients
                                        if connection is not self:
                                            data["username"] = self.account["display"]
                                            connection.send(**data)  # formats the dictionary into kwargs
                                else:
                                    self.send(
                                        type="message",
                                        emphasis="WARNING",
                                        content="Client not authorised to send emphasis messages."
                                    )

                            else:
                                self.send(
                                    type="message",
                                    emphasis="WARNING",
                                    content="Client not authenticated"
                                )
                                self.send(type="desist from existence")
                except KeyError as e:
                    print("ignoring exception in run(); KeyError:", e)
                    self.send(
                        type="message",
                        emphasis="WARNING",
                        content="Invalid communication"
                    )

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
