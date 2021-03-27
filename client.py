import threading
import socket


class Connection(threading.Thread):
    def __init__(self, address):
        super().__init__()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(address)

    def run(self) -> None:
        while True:
            try:
                data = self.sock.recv(1024)
                print(data.decode())

            except ConnectionError as e:
                print(e)
                break


server = Connection(("127.0.0.1", 3952))
server.start()

running = True

while running:
    client_input = input()

    if server.is_alive():
        server.sock.send(client_input.encode())

    else:
        running = False
