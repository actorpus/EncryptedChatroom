import random
import pickle
from typing import *


class Communication:
    def __init__(self, sock, save_requests=True):
        self.active_packets = {}
        self.save_requests = save_requests
        if self.save_requests:
            self.requested_data = {}
        self.sock = sock

    @staticmethod
    def encrypt(data, key):
        return b''.join([((x[0] + x[1]) % 255).to_bytes(1, "big") for x in zip(data, key)])

    @staticmethod
    def decrypt(data, key):
        return b''.join([((x[0] - x[1]) % 255).to_bytes(1, "big") for x in zip(data, key)])

    @staticmethod
    def gen_key(length: int) -> bytes:
        return b''.join([random.randint(0, 255).to_bytes(1, "big") for _ in range(length)])

    def send(self, type, **kwargs):
        if self.save_requests:
            if type == 5:
                for key in kwargs.keys():
                    self.requested_data[key] = False

        kwargs["type"] = type

        data = pickle.dumps(kwargs)

        packet_key = self.gen_key(len(data))
        packet_id = self.gen_key(2)
        packet_state = b'\x00'

        data = packet_state + packet_id + self.encrypt(data, packet_key)

        self.active_packets[packet_id] = packet_key

        self.sock.send(data)

    def recv(self, buffer_size) -> Union[None, dict]:
        data = self.sock.receive(buffer_size)

        packet_state = data[0]
        packet_id = data[1:3]
        data = data[3:]

        if packet_state == 0:
            packet_key = self.gen_key(len(data))

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

            if self.save_requests:
                if ret["type"] == 5:
                    for key in ret:
                        if key != "type":
                            self.requested_data[key] = ret[key]

            return ret

    def get_requested_data(self):
        for key in self.requested_data:
            if not self.requested_data is None:
                return key, self.requested_data[key]
