import socket
import threading
import random


xor_bytes = lambda a, b: b''.join([(x[0] ^ x[1]).to_bytes(1, "big") for x in zip(a, b)])


IP = ""
PORT = 3952

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((IP, PORT))
sock.listen(4)

lock = threading.Lock()
servers = []


class Connection(threading.Thread):
    def __init__(self, addresses):
        super().__init__()
        self.sock: socket.socket = addresses[0]
        self.address: tuple[str, int] = addresses[1]

        self.active_packets = {}

        lock.acquire()
        servers.append(self)
        lock.release()

    def send(self, data: bytes):
        packet_key = random.randbytes(len(data))
        packet_id = random.randbytes(2)
        packet_state = b'\x03'

        data = packet_state + packet_id + xor_bytes(data, packet_key)

        self.active_packets[packet_id] = packet_key

        self.sock.send(data)

    def recv(self, data: bytes):
        packet_state = data[0]
        packet_id = data[1:3]
        data = data[3:]

        if packet_state == 0:
            packet_key = random.randbytes(len(data))

            data = xor_bytes(data, packet_key)
            self.active_packets[packet_id] = packet_key

            data = b'\x01' + packet_id + data

            self.sock.send(data)

        elif packet_state == 2:
            packet_key = self.active_packets[packet_id]

            data = xor_bytes(data, packet_key)

            del self.active_packets[packet_id]

            return data

        elif packet_state == 4:
            packet_key = self.active_packets[packet_id]

            data = xor_bytes(data, packet_key)

            data = b'\x05' + packet_id + data

            self.sock.send(data)

    def run(self):
        while True:
            try:
                data = self.sock.recv(1024)
                message = self.recv(data)

                if message is not None:
                    print(message)

                    self.send(message)

            except ConnectionError as e:
                print(e)
                break

        lock.acquire()
        servers.remove(self)
        lock.release()

while True:
    con = sock.accept()
    Connection(con).start()
