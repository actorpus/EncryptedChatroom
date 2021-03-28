import threading
import socket
import random
import pickle
import os


encrypt = lambda a, b: b''.join([((x[0] + x[1]) % 255).to_bytes(1, "big") for x in zip(a, b)])
decrypt = lambda a, b: b''.join([((x[0] - x[1]) % 255).to_bytes(1, "big") for x in zip(a, b)])


class Connection:
    def __init__(self, address, credentials, ignore_desist_from_existence: bool = False):
        self.ignore_desist_from_existence = ignore_desist_from_existence

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(address)

        self.credentials = credentials

        self.active_packets = {}

        self.input = True
        threading.Thread(target=self.input_loop).start()

        self.run()

    def input_loop(self):
        while self.input:
            inp = input()
            if inp:
                if inp[0] == "$":
                    try:
                        exec(inp[1:])
                    except Exception as e:
                        print(e)
                else:
                    self.send(
                        type="message",
                        emphasis=None,  # used for formats
                        content=inp
                    )

    def send(self, **kwargs):
        data = pickle.dumps(kwargs)

        packet_key = random.randbytes(len(data))
        packet_id = random.randbytes(2)
        packet_state = b'\x00'

        data = packet_state + packet_id + encrypt(data, packet_key)

        self.active_packets[packet_id] = packet_key

        self.sock.send(data)

    def recv(self, data: bytes):
        packet_state = data[0]
        packet_id = data[1:3]
        data = data[3:]

        if packet_state == 1:
            packet_key = self.active_packets[packet_id]

            data = decrypt(data, packet_key)

            data = b'\x02' + packet_id + data

            del self.active_packets[packet_id]

            self.sock.send(data)

        elif packet_state == 3:
            packet_key = random.randbytes(len(data))

            data = encrypt(data, packet_key)
            self.active_packets[packet_id] = packet_key

            data = b'\x04' + packet_id + data

            self.sock.send(data)

        elif packet_state == 5:
            packet_key = self.active_packets[packet_id]

            data = decrypt(data, packet_key)

            del self.active_packets[packet_id]

            return data

    @staticmethod
    def forcefully_exit(exit_code: int = 0):
        os._exit(exit_code)
        # ignore error its a protected function
        # also don't use this ever ;)

    def run(self) -> None:
        self.send(
            type="authenticate",
            username=self.credentials[0],
            password=self.credentials[1]
        )

        while True:
            try:
                data = self.sock.recv(1024)
                message = self.recv(data)

                if message is not None:
                    data = pickle.loads(message)

                    if data["type"] == "message":
                        if data["emphasis"] is None:
                            print(data["username"] + " > " + data["content"])

                        elif data["emphasis"] == "WARNING":
                            print("\033[31mWARNING: %s\033[0m" % data["content"])

                        elif data["emphasis"] == "CONFIRMATION":
                            print("\033[34mCONFIRMATION: %s\033[0m" % data["content"])

                    elif data["type"] == "desist from existence":
                        if not self.ignore_desist_from_existence:
                            self.forcefully_exit()

                    elif data["type"] == "authentication confirmation":
                        print("\033[34mClient authenticated\033[0m")

            except KeyboardInterrupt:
                print("Keyboard interrupt")
                self.forcefully_exit()

            except ConnectionResetError:
                print("Lost connection to server")
                self.forcefully_exit()

os.system("color 4")  # initialise colour
print("\033[0m", end="")  # reset color

username = input("username > ")
password = input("password > ")

server = Connection(("127.0.0.1", 3952), (username, password))
