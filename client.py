import threading
import socket
import os
import msvcrt
import security
import ctypes
import time

MESSAGE = 0
DESIST_FROM_EXISTENCE = 1
AUTHENTICATE = 2
AUTHENTICATION_CONFIRMATION = 3
UPDATE_PROFILE = 4
REQUEST_DATA = 5

SetCursorPos = ctypes.windll.user32.SetCursorPos
mouse_event = ctypes.windll.user32.mouse_event

default_colours = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[0m"
}


def silent_input(*args, fill="", end="\n"):
    """
    Creates an input option which allows users to hide their password from watchful eyes - password security.
    :param Tuple[Any] args: The argument
    :param str fill:
    :param str end:
    :return:
    """
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
            print("Could not connect to server %s:%s" % address)
            return

        self.credentials = credentials

        self.communication = security.Communication(self.sock)

        self.input = True
        threading.Thread(target=self.input_loop).start()

        self.run()

    def input_loop(self) -> None:
        """
        A threaded method which allows the client to send packets of each key press to the server.
        :return: Once the server has understood and sent back a message, something occurs depending on user input.
        """
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
                                display=inp[10:],
                            )
                    elif inp[:7] == "/colour":
                        try:
                            colour_change = default_colours[inp[8:].strip()]
                            self.communication.send(
                                type=UPDATE_PROFILE,
                                colour=colour_change
                            )
                        except KeyError:
                            print("Could not change text to " + inp[8:].strip() + ". \nChoose from:\n* " +
                                  "\n* ".join([default_colours[colour] + colour + default_colours["white"] for colour in
                                               default_colours.keys()]))

                    elif inp.strip() == "/quit":
                        print("Goodbye")
                        time.sleep(1.5)
                        self.forcefully_exit()

                    elif inp.strip() == "/help":
                        print("""
All available commands:
\t\\help\t\t-\tBrings up a list of all commands.
\t\\colour\t\t-\tChanges the colour of the messages you receive.
\t\t\t\tYou can choose from RGB to CYM(K) colours.
\t\\quit\t\t-\tTerminates your connection with the server.
\t\\:thumbs up:\t\t-\t Displays an ascii art of a thumbs up - created by 'ChTrSrFr'
""")

                elif ":thumbs up:" in inp:
                    self.communication.send(
                        type=MESSAGE,
                        emphasis=None,
                        content=inp,
                        ascii_art=True
                    )

                else:
                    self.communication.send(
                        type=MESSAGE,
                        emphasis=None,  # used for formats (normally disallowed for clients)
                        content=inp,
                        ascii_art=False
                    )

    @staticmethod
    def forcefully_exit(exit_code: int = 0) -> None:
        """
        Terminates all threads and connections.
        :param int exit_code: The exit code .
        :return: None.
        """
        print("\033[31mYou have been kicked from the server...\033[0m")
        time.sleep(1)
        os._exit(exit_code)
        # ignore error it's a protected function
        # also don't use this ever ;)

    def run(self) -> None:
        """
        Runs the client, and handles their inputs.
        :return: None.
        """
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
