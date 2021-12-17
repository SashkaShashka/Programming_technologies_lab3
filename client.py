from socket import *
import sys
import json
import time

def continue_client(client_state, on_start=False):
    global clientSocket
    # client_state False - ответ клиента не был принят, True - был принят и клиент ждёт ответа другого игрока и результатов

    if not client_state:
        try:
            if on_start:
                serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # except никогда не сработает
                print(serverMessage)  # Ожидание другого игрока or С вами тут играть не хотят
                if (serverMessage == 'Ожидание другого игрока'):
                    pass
                else:
                    clientSocket.close()
                    sys.exit()

            serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # введите ход
            print(serverMessage)

            serverMessage = ''
            while serverMessage != 'Ваш ход принят. Ждите пока соперник ответит':
                clientMessage = input()
                clientSocket.send(json.dumps(clientMessage).encode("utf-8"))
                serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # ожидайте или ход не распознан
                print(serverMessage)

            client_state = True
            serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # ход соперника
            print(serverMessage)

            # не будет except -> не будет отключ сервра -> не будет состояния, когда ход соперника отправлен, а результат нет

            serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # исход игры
            print(serverMessage)
            clientSocket.close()
            sys.exit()
        except Exception as e1:
            print('Соединение с сервером потеряно, попытка подключиться снова')
            clientSocket = socket(AF_INET, SOCK_STREAM)
            clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            clientSocket.bind(('127.0.0.1', clientSocket_name))

            connection_flag = False
            tic = time.perf_counter()
            while time.perf_counter() - tic < 5:
                try:
                    clientSocket.connect((hostIp, portNumber))
                    print('Подключение установлено, продолжение игры')
                    connection_flag = True
                    break
                except Exception as e2:
                    pass
            if connection_flag:
                continue_client(client_state)  # продолжение игры с сохр сост
            else:
                print('Время подключения вышло, завершение работы')
                clientSocket.close()
                sys.exit()
    else:
        serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # ход соперника
        print(serverMessage)

        # не будет except -> не будет отключ сервра -> не будет состояния, когда ход соперника отправлен, а результат нет

        serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # исход игры
        print(serverMessage)
        clientSocket.close()
        sys.exit()

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

hostIp = "127.0.0.1"
portNumber = 9090

try:
    clientSocket.connect((hostIp, portNumber))
    clientSocket_name = clientSocket.getsockname()[1]
except Exception:
    print('Сервер не активен, попробуйте подключиться позже')
    clientSocket.close()
    sys.exit()

client_state = False  # False - ответ клиента не был принят, True - был принят и клиент ждёт ответа другого игрока и результатов

continue_client(client_state, True)

'''
try:
    serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # except никогда не сработает
    print(serverMessage)  # Ожидание другого игрока or С вами тут играть не хотят
    if (serverMessage=='Ожидание другого игрока'):
        serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # введите ход
        print(serverMessage)

        serverMessage = ''
        while serverMessage != 'Ваш ход принят. Ждите пока соперник ответит':
            clientMessage = input()
            clientSocket.send(json.dumps(clientMessage).encode("utf-8"))

            serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # ожидайте или ход не распознан
            print(serverMessage)

        client_state = True

        serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # ход соперника
        print(serverMessage)

        # не будет except -> не будет отключ сервра -> не будет состояния, когда ход соперника отправлен, а результат нет

        serverMessage = json.loads(clientSocket.recv(1024).decode("utf-8"))  # исход игры
        print(serverMessage)

    clientSocket.close()
    sys.exit()
except Exception as e1:
    print('Соединение с сервером потеряно, попытка подключиться снова')

    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    clientSocket.bind(('127.0.0.1', clientSocket_name))
    while True:
        try:
            clientSocket.connect((hostIp, portNumber))
            print('Подключение установлено, продолжение игры')
            break
        except Exception as e2:
            pass
    continue_client(client_state)  # продолжение игры с сохр сост
'''
