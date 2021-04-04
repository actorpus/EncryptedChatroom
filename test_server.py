import SecurityV2

server = SecurityV2.SecureSocketWrapper.Server(("", 19875))

connection = server.accept()

while True:
    try:
        print(connection.receive(1024))

    except SecurityV2.Errors.SecurityAbortError:
        break
