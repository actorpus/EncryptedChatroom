import threading
import socket
import random


xor_bytes = lambda a, b: b''.join([(x[0] ^ x[1]).to_bytes(1, "big") for x in zip(a, b)])


class Connection(threading.Thread):
    def __init__(self, address):
        super().__init__()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(address)

        self.active_packets = {}

    def send(self, data: bytes):
        packet_key = random.randbytes(len(data))
        packet_id = random.randbytes(2)
        packet_state = b'\x00'

        data = packet_state + packet_id + xor_bytes(data, packet_key)

        self.active_packets[packet_id] = packet_key

        self.sock.send(data)

    def recv(self, data: bytes):
        packet_state = data[0]
        packet_id = data[1:3]
        data = data[3:]

        if packet_state == 1:
            packet_key = self.active_packets[packet_id]

            data = xor_bytes(data, packet_key)

            data = b'\x02' + packet_id + data

            self.sock.send(data)

        elif packet_state == 3:
            packet_key = random.randbytes(len(data))

            data = xor_bytes(data, packet_key)
            self.active_packets[packet_id] = packet_key

            data = b'\x04' + packet_id + data

            self.sock.send(data)

        elif packet_state == 5:
            packet_key = self.active_packets[packet_id]

            data = xor_bytes(data, packet_key)

            del self.active_packets[packet_id]

            return data

    def run(self) -> None:
        while True:
            try:
                data = self.sock.recv(1024)
                message = self.recv(data)

                if message is not None:
                    print(message)

            except ConnectionError as e:
                print(e)
                break


server = Connection(("127.0.0.1", 3952))
server.start()

running = True

while running:
    client_input = input()

    if server.is_alive():
        server.send(client_input.encode())

    else:
        running = False
