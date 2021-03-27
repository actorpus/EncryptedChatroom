import socket
import threading


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

        lock.acquire()
        servers.append(self)
        lock.release()

    def run(self):
        while True:
            try:
                data = self.sock.recv(1024)

            except ConnectionError as e:
                print(e)
                break

            self.sock.send(data)

        lock.acquire()
        servers.remove(self)
        lock.release()

while True:
    con = sock.accept()
    Connection(con).start()
