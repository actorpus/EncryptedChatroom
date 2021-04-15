"""
STILL EXPERIMENTAL
"""

import SecurityV2
import threading
import logging
import socket
import random

logging.basicConfig(filename="test.log", level=logging.INFO, format="%(levelname)s@%(name)s:%(message)s")


users = {  # temporary
    "AE12F0": {
        "pass": "password"
    }
}


class connection(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("Tread(connection)[%s]" % sock.address[0])
        self.sock = sock

        lock.acquire()
        connections.append(self)
        lock.release()

        self.logger.debug("added self to connections list")

        self.start()

    def run(self):
        self.logger.debug("waiting for authentication packet")

        login: dict = self.sock.receive(1024)

        self.logger.debug("authentication packet received: %s" % str(login))

        if login["uuid"] in users.keys() and users[login["uuid"]]["pass"] == login["pass"]:
            self.logger.info("client passed authentication")

            while True:
                try:
                    self.logger.debug("waiting for data")

                    data = self.sock.receive(1024)

                    self.logger.debug("data received: %s" % str(data))

                except ConnectionResetError:
                    self.logger.info("client closed connection")
                    break

                data["uuid"] = login["uuid"]
                self.logger.debug("added uuid to packet")

                for con in connections:
                    # note: sends back to sender to allow for delay calculation and the client receives current
                    # stats about self
                    con.sock.send(data)
                    self.logger.debug("sent data to %s" % str(con.sock.address))

        else:
            self.logger.info("client failed authentication")

            self.sock.close()

        lock.acquire()
        connections.remove(self)
        lock.release()

        self.logger.debug("removed self from connections")


class WebServerRedirect(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.web_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.web_server.bind(("", 80))
        self.web_server.listen(1)

        self.start()

    def run(self) -> None:
        while True:
            c, _ = self.web_server.accept()

            c.recv(2048)  # ignore incoming data, its probably a GET request

            c.send(b"HTTP/1.1 307 Temporary Redirect\r\nLocation: http://actorpus.github.io/enc.html\r\n\r\n")
            # redirect any http clients to a info site
            # use temporary redirect here to avoid caching problems

            c.close()


class InputLoop(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.start()

    def run(self) -> None:
        while True:
            i = input()

            if i == "create user":
                uuid = hex(random.getrandbits(24))[2:].upper().rjust(6, "0")
                pas = input("uuid > %s\npass > " % uuid)

                lock.acquire()
                users[uuid] = {"pass": pas}
                lock.release()

                print(users)

connections = []
lock = threading.Lock()

ADDRESS = "localhost", 3953  # hosts file to check destination
server = SecurityV2.SecureSocketWrapper.Server(ADDRESS)

logging.info("Created socket ADDRESS:%s" % str(ADDRESS))

WebServerRedirect()
InputLoop()

while True:
    c = server.accept()

    logging.info("accepted connection from %s" % str(c.address))

    connection(c)
