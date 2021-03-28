import random
import pickle
from typing import *


class Communication:
    def __init__(self, sock):
        self.active_packets = {}
        self.sock = sock

    @staticmethod
    def encrypt(data, key):
        return b''.join([((x[0] + x[1]) % 255).to_bytes(1, "big") for x in zip(data, key)])

    @staticmethod
    def decrypt(data, key):
        return b''.join([((x[0] - x[1]) % 255).to_bytes(1, "big") for x in zip(data, key)])

    def send(self, **kwargs):
        data = pickle.dumps(kwargs)

        packet_key = random.randbytes(len(data))
        packet_id = random.randbytes(2)
        packet_state = b'\x00'

        data = packet_state + packet_id + self.encrypt(data, packet_key)

        self.active_packets[packet_id] = packet_key

        self.sock.send(data)

    def recv(self, buffer_size) -> Union[None, dict]:
        data = self.sock.recv(buffer_size)

        packet_state = data[0]
        packet_id = data[1:3]
        data = data[3:]

        if packet_state == 0:
            packet_key = random.randbytes(len(data))

            data = self.encrypt(data, packet_key)

            self.active_packets[packet_id] = packet_key

            data = b'\x01' + packet_id + data

            self.sock.send(data)

        elif packet_state == 1:
            packet_key = self.active_packets[packet_id]

            data = self.decrypt(data, packet_key)

            data = b'\x02' + packet_id + data

            del self.active_packets[packet_id]

            self.sock.send(data)

        elif packet_state == 2:
            packet_key = self.active_packets[packet_id]

            data = self.decrypt(data, packet_key)

            del self.active_packets[packet_id]

            ret: dict = pickle.loads(data)

            return ret
