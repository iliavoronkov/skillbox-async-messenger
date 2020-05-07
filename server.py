"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                my_login = decoded.replace("login:", "").replace("\r\n", "")
                login_found = False
                for login_used in self.server.clients:
                    if login_used.login == my_login:
                        login_found = True
                        break

                if login_found:
                    self.transport.write(
                    f"Логин {my_login} занят, попробуйте другой".encode())
                    self.transport.close()
                else:
                    self.login = my_login
                    self.transport.write(
                    f"Привет, {self.login}!".encode())
                    self.server.logins.append(self.login)
                    self.send_history()
        else:
            self.send_message(decoded)

    def send_history(self):
        if len(self.server.last_messages) > 0:
            self.transport.write(f"Последние сообщения:\r\n".encode())
            for lastmes in self.server.last_messages:
                self.transport.write(lastmes)
                self.transport.write("\r\n".encode())
            self.transport.write(f"====================".encode())

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.server.last_messages.append(encoded)
        if len(self.server.last_messages)>10:
            self.server.last_messages.pop(0)


        for client in self.server.clients:
            if (client.login != self.login) and (not client.login is None):
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        try:
            self.server.clients.remove(self)
            self.server.logins.remove(self.login)
        except ValueError:
            print("Соединение разорвано сервером")
        print("Соединение разорвано")


class Server:
    clients: list
    last_messages : list

    def __init__(self):
        self.clients = []
        self.logins = []
        self.last_messages = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
