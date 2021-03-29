import threading
import socket
import os
import msvcrt
import security


MESSAGE = 0
DESIST_FROM_EXISTENCE = 1
AUTHENTICATE = 2
AUTHENTICATION_CONFIRMATION = 3
UPDATE_PROFILE = 4
REQUEST_DATA = 5


def silent_input(*args, fill="", end="\n"):
    print(*args, end="", flush=True)

    static = ''
    while True:
        x = msvcrt.getch()

        if x == b'\r':
            print(end=end)
            return static

        elif x == b'\x08':
            static = static[:-1]

        else:
            static += x.decode()
            print(fill, end="", flush=True)


class Connection:
    def __init__(self, address, credentials, ignore_desist_from_existence: bool = False):
        self.ignore_desist_from_existence = ignore_desist_from_existence

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect(address)

        except ConnectionRefusedError:
            print("could not connect to server %s:%s" % address)
            return

        self.credentials = credentials

        self.communication = security.Communication(self.sock)

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

                elif inp[0] == "/":
                    if inp[:9] == "/username":
                        if inp[10:]:
                            self.communication.send(
                                type=UPDATE_PROFILE,
                                display=inp[10:]
                            )

                else:
                    self.communication.send(
                        type=MESSAGE,
                        emphasis=None,  # used for formats (normally disallowed for clients)
                        content=inp
                    )

    @staticmethod
    def forcefully_exit(exit_code: int = 0):
        os._exit(exit_code)
        # ignore error its a protected function
        # also don't use this ever ;)

    def run(self) -> None:
        self.communication.send(
            type=AUTHENTICATE,
            username=self.credentials[0],
            password=self.credentials[1]
        )

        while True:
            try:
                data = self.communication.recv(1024)

                if data is not None:
                    if data["type"] == MESSAGE:
                        if data["emphasis"] is None:
                            print(data["username"] + " > " + data["content"])

                        elif data["emphasis"] == "WARNING":
                            print("\033[31mWARNING: %s\033[0m" % data["content"])

                        elif data["emphasis"] == "CONFIRMATION":
                            print("\033[34mCONFIRMATION: %s\033[0m" % data["content"])

                    elif data["type"] == DESIST_FROM_EXISTENCE:
                        if not self.ignore_desist_from_existence:
                            self.forcefully_exit()

                    elif data["type"] == AUTHENTICATION_CONFIRMATION:
                        print("\033[34mClient authenticated\033[0m")

                    elif data["type"] == REQUEST_DATA:
                        print(data)

            except KeyboardInterrupt:
                print("Keyboard interrupt")
                self.forcefully_exit()

            except ConnectionResetError:
                print("Lost connection to server")
                self.forcefully_exit()


os.system("color 4")  # initialise colour (windows only)
print("\033[0m", end="")  # reset color

ip_address = input("address > ")
username = input("username > ")
password = [silent_input, input]["`PYTHONUNBUFFERED`" in os.environ.keys()]("password > ")

Connection((ip_address, 3952), (username, password))
