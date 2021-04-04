import SecurityV2

client = SecurityV2.SecureSocketWrapper.Client(("127.0.0.1", 19875))

client.send(
    ["th", 1, "s", ("is", "a", "test", (0,), "f", "security!")]
)

while True:
    i = input()
    client.send(i)
