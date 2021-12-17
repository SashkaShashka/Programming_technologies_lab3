import socket
from socket import *
import concurrent.futures
import json
import time
import threading
import sys
import os.path
from jsonschema import Draft7Validator


class ThreadCloseSocket(threading.Thread):
    def __init__(self, hostSocket):
        super(ThreadCloseSocket, self).__init__()
        self.hostSocket=hostSocket

    def run(self):
        while True:
            try:
                clientSocket, clientAddress = self.hostSocket.accept()
                clientSocket.send(json.dumps('С вами тут играть не хотят').encode("utf-8"))
                clientSocket.close()
            except Exception as e:
                pass


def send_message(player, message):
    global param_list
    try:
        param_list[player][0].send(json.dumps(message).encode("utf-8"))
        time.sleep(0.1)
    except Exception as e:
        print('Не получилось отправить сообщение игроку', player)


def clientThread(clientParams):
    global answers
    global param_list
    global clients

    clientSocket, clientAddress, i = clientParams  # извлекаем i (done)
    try:
        clientSocket.send(json.dumps('Выберите камень / ножницы / бумага: ').encode("utf-8"))
        while True:
            answer = json.loads(clientSocket.recv(1024).decode("utf-8"))
            if answer == 'камень' or answer == 'ножницы' or answer == 'бумага':
                clientSocket.send(json.dumps('Ваш ход принят. Ждите пока соперник ответит').encode("utf-8"))
                break
            else:
                clientSocket.send(json.dumps('Ход ' + answer + ' не распознан. Введите один из вариантов: камень / ножницы / бумага').encode("utf-8"))

    except Exception as e:
        clients.remove(clientSocket)
        print(clientAddress[0] + ":" + str(clientAddress[1]) + " disconnected")
        print('clientThread: ', clientAddress, ' error: ', e)
        answer = 'disconnected'
        clientSocket.close()

    answers[i] = answer
    # обновляем состояние сервера + состояние игрока (когда ожидайте - answer) (done)
    if answers[i] == 'disconnected':
        if answers[1-i] == 'не принят ответ':
            # записать server_state.json (done)

            with open('server_state.json', 'r') as f:
                server_state = json.load(f)

            data = {}
            data['client{}'.format(i)] = {
                'status': 'disconnected'
            }
            data['client{}'.format(1-i)] = {
                'status': 'не принят ответ',
                'address': server_state['client{}'.format(1-i)]['address'],  # param_list[1 - i][1][0],
                'socket': server_state['client{}'.format(1 - i)]['socket']  # param_list[1 - i][1][1]
            }
            with open('server_state.json', 'w') as f:
                json.dump(data, f, ensure_ascii=False)
    elif answers[i] == 'не принят ответ':
        if answers[1 - i] == 'disconnected':
            # записать server_state.json (done)

            with open('server_state.json', 'r') as f:
                server_state = json.load(f)

            data = {}
            data['client{}'.format(1-i)] = {
                'status': 'disconnected'
            }
            data['client{}'.format(i)] = {
                'status': 'не принят ответ',
                'address': server_state['client{}'.format(i)]['address'],  # param_list[i][1][0],
                'socket': server_state['client{}'.format(i)]['socket']  # param_list[i][1][1]
            }
            with open('server_state.json', 'w') as f:
                json.dump(data, f, ensure_ascii=False)
    elif answers[i] == 'камень' or answers[i] == 'ножницы' or answers[i] == 'бумага':
        if answers[1 - i] == 'не принят ответ':

            with open('server_state.json', 'r') as f:
                server_state = json.load(f)

            data = {}
            data['client{}'.format(1 - i)] = {
                'status': 'не принят ответ',
                'address': server_state['client{}'.format(1-i)]['address'],
                'socket': server_state['client{}'.format(1-i)]['socket']
            }
            data['client{}'.format(i)] = {
                'status': answers[i],
                'address': server_state['client{}'.format(i)]['address'],
                'socket': server_state['client{}'.format(i)]['socket']
            }
            with open('server_state.json', 'w') as f:
                json.dump(data, f, ensure_ascii=False)
    elif answers[1-i] == 'камень' or answers[1-i] == 'ножницы' or answers[1-i] == 'бумага':
        if answers[i] == 'не принят ответ':

            with open('server_state.json', 'r') as f:
                server_state = json.load(f)

            data = {}
            data['client{}'.format(i)] = {
                'status': 'не принят ответ',
                'address': server_state['client{}'.format(i)]['address'],
                'socket': server_state['client{}'.format(i)]['socket']
            }
            data['client{}'.format(1-i)] = {
                'status': answers[1-i],
                'address': server_state['client{}'.format(1-i)]['address'],
                'socket': server_state['client{}'.format(1-i)]['socket']
            }
            with open('server_state.json', 'w') as f:
                json.dump(data, f, ensure_ascii=False)


def new_game():
    global answers
    global param_list
    global clients

    clients = list()

    hostSocket = socket(AF_INET, SOCK_STREAM)
    hostSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    hostIp = "127.0.0.1"
    portNumber = 9090
    hostSocket.bind((hostIp, portNumber))
    hostSocket.listen()
    print("Waiting for connection...")

    param_list = list()
    for i in range(2):
        clientSocket, clientAddress = hostSocket.accept()
        clients.append(clientSocket)
        clientSocket.send(json.dumps('Ожидание другого игрока').encode("utf-8"))
        print("Connection established with: ", clientAddress[0] + ":" + str(clientAddress[1]))

        param_list.append((clientSocket, clientAddress, i))  # добавляем i (done)
        data = {}
        data['client1'] = {
            'status': 'disconnected'
        }
        data['client0'] = {
            'status': 'не принят ответ',
            'address': param_list[0][1][0],
            'socket': param_list[0][1][1]
        }
        with open('server_state.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False)


    #print('param_list[1][1]: ', param_list[1][1])
    #print('param_list[1][0]: ', param_list[1][0])
    #print('param_list[1]: ', param_list[1])
    #print('socket0 int type: ', type(int(param_list[1][0])))
    #print('socket0 int: ', int(param_list[1][0]))
    data = {}
    data['client1'] = {
        'status': 'не принят ответ',
        'address': param_list[1][1][0],
        'socket': param_list[1][1][1]
    }
    data['client0'] = {
        'status': 'не принят ответ',
        'address': param_list[0][1][0],
        'socket': param_list[0][1][1]
    }
    with open('server_state.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)

    answers = ['не принят ответ', 'не принят ответ']

    t1 = ThreadCloseSocket(hostSocket)
    t1.daemon = True
    t1.start()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(clientThread, param) for param in param_list]

    a = {
        "камень": "ножницы",
        "ножницы": "бумага",
        "бумага": "камень"
    }

    b = answers[0]
    c = answers[1]

    if b == 'disconnected' and b != c:
        print('Один из игроков отключился, игра отменена')
        send_message(1, '\nСоперник не сделал ход')
        send_message(1, 'Соперник отключился, игра отменена')
    elif c == 'disconnected' and b != c:
        print('Один из игроков отключился, игра отменена')
        send_message(0, '\nСоперник не сделал ход')
        send_message(0, 'Соперник отключился, игра отменена')
    elif c == 'disconnected' and b == 'disconnected':
        print("Оба игрока отключились, игра отменена")
    else:
        print('Ход игрока 1:', b)
        print('Ход игрока 2:', c)

        send_message(0, '\nХод соперника: ' + c)
        send_message(1, '\nХод соперника: ' + b)

        if b == c:
            print("Ничья")
            send_message(0, 'Ничья')
            send_message(1, 'Ничья')
        for i, j in a.items():
            if b == i and c == j:
                print("Победил Игрок 1")
                send_message(0, 'Вы победили')
                send_message(1, 'Вы проиграли')
            elif c == i and b == j:
                print("Победил Игрок 2")
                send_message(0, 'Вы проиграли')
                send_message(1, 'Вы победили')

        for i in range(len(clients)):
            try:
                clients[i].close()
            except Exception as e:
                pass

    # удалить файл
    os.remove('server_state.json')

    hostSocket.close()
    sys.exit()

def continue_game(player_num, ans, client_socket, client_address):
    global answers
    global param_list
    global clients

    clients = list()

    hostSocket = socket(AF_INET, SOCK_STREAM)
    hostSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    hostSocket.settimeout(0.05)

    hostIp = "127.0.0.1"
    portNumber = 9090
    hostSocket.bind((hostIp, portNumber))
    hostSocket.listen()
    print("Waiting for connection...")

    param_list = list()

    tic = time.perf_counter()
    while time.perf_counter() - tic < 10:  # ждать определенное количество времени, а не всегда (случай когда клиент был, но отвалился) (done)
        try:
            clientSocket, clientAddress = hostSocket.accept()
            if clientAddress[1] == client_socket and clientAddress[0] == client_address:
                clients.append(clientSocket)
                param_list.append((clientSocket, clientAddress, player_num))  # добавляем i (done)
                break
            else:
                clientSocket.send(json.dumps('С вами тут играть не хотят').encode("utf-8"))
                clientSocket.close()

        except Exception as e:
            pass

    if len(clients) == 0:
        # написать выход (done)
        print('Все отключились, никто не выжил')
        os.remove('server_state.json')
        hostSocket.close()
        sys.exit()

    answers = ['disconnected', 'disconnected']
    answers[player_num] = 'не принят ответ'

    t1 = ThreadCloseSocket(hostSocket)
    t1.daemon = True
    t1.start()

    clientSocket, clientAddress, i = param_list[0]  # извлекаем i (done)
    try:
        clientSocket.send(json.dumps('Выберите камень / ножницы / бумага: ').encode("utf-8"))
        while True:
            answer = json.loads(clientSocket.recv(1024).decode("utf-8"))
            if answer == 'камень' or answer == 'ножницы' or answer == 'бумага':
                clientSocket.send(json.dumps('Ваш ход принят. Ждите пока соперник ответит').encode("utf-8"))
                break
            else:
                clientSocket.send(json.dumps(
                    'Ход ' + answer + ' не распознан. Введите один из вариантов: камень / ножницы / бумага').encode(
                    "utf-8"))
    except Exception as e:
        clients.remove(clientSocket)
        print(clientAddress[0] + ":" + str(clientAddress[1]) + " disconnected")
        answer = 'disconnected'
        clientSocket.close()
    answers[player_num] = answer
    # надо удалять сост игроков?

    a = {
        "камень": "ножницы",
        "ножницы": "бумага",
        "бумага": "камень"
    }

    b = answers[0]
    c = answers[1]

    if b == 'disconnected' and b != c:
        print('Один из игроков отключился, игра отменена')
        send_message(0, '\nСоперник не сделал ход')
        send_message(0, 'Соперник отключился, игра отменена')
    elif c == 'disconnected' and b != c:
        print('Один из игроков отключился, игра отменена')
        send_message(0, '\nСоперник не сделал ход')
        send_message(0, 'Соперник отключился, игра отменена')
    elif c == 'disconnected' and b == 'disconnected':
        print("Оба игрока отключились, игра отменена")

    # удалить файл (done)
    os.remove('server_state.json')

    hostSocket.close()
    sys.exit()


def continue_game_2_players_without_answers(clients_sockets, clients_addresses):
    global answers
    global param_list
    global clients

    clients = list()

    hostSocket = socket(AF_INET, SOCK_STREAM)
    hostSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    hostSocket.settimeout(0.05)

    hostIp = "127.0.0.1"
    portNumber = 9090
    hostSocket.bind((hostIp, portNumber))
    hostSocket.listen()
    print("Waiting for connection...")

    param_list = list()

    answers = ['не принят ответ', 'не принят ответ']

    connected = -1  # -1 - никто не подключен, 0 - подключен 0, 1 - подключен 1, 2 - подключены все

    place_0_in_param_list = -1
    place_1_in_param_list = -1

    tic = time.perf_counter()
    while time.perf_counter() - tic < 10:  # ждать определенное количество времени, а не всегда (случай когда клиент был, но отвалился) (done)
        try:
            clientSocket, clientAddress = hostSocket.accept()

            if connected != 0 and clientAddress[1] == clients_sockets[0] and clientAddress[0] == clients_addresses[0]:
                clients.append(clientSocket)
                param_list.append((clientSocket, clientAddress, 0))  # добавляем i=len(clients)-1 (done)
                place_0_in_param_list = len(param_list)-1
                if connected == 1:
                    connected = 2
                    break
                else:
                    connected = 0
            if connected != 1 and clientAddress[1] == clients_sockets[1] and clientAddress[0] == clients_addresses[1]:
                clients.append(clientSocket)
                param_list.append((clientSocket, clientAddress, 1))  # добавляем i=len(clients)-1 (done)
                place_1_in_param_list = len(param_list)-1
                if connected == 0:
                    connected = 2
                    break
                else:
                    connected = 1
            if not (clientAddress[1] == clients_sockets[0] and clientAddress[0] == clients_addresses[0] or clientAddress[1] == clients_sockets[1] and clientAddress[0] == clients_addresses[1]):
                clientSocket.send(json.dumps('С вами тут играть не хотят').encode("utf-8"))
                clientSocket.close()
        except Exception as e:
            pass

    if connected == -1:
        # все отключились, никто не выжил - написать конец проги (done)
        print('Продолжить игру не удалось, клиенты отключились. Завершение работы сервера.')
        os.remove('server_state.json')
        hostSocket.close()
        sys.exit()
    elif connected == 0:
        answers[1] = 'disconnected'
        data = {}
        data['client1'] = {
            'status': 'disconnected'
        }
        data['client0'] = {
            'status': 'не принят ответ',
            'address': param_list[place_0_in_param_list][1][0],
            'socket': param_list[place_0_in_param_list][1][1]
        }
        with open('server_state.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False)
        continue_game(0, 'не принят ответ', clients_sockets[0], clients_addresses[0])

    elif connected == 1:
        answers[0] = 'disconnected'
        data = {}
        data['client0'] = {
            'status': 'disconnected'
        }
        data['client1'] = {
            'status': 'не принят ответ',
            'address': param_list[place_1_in_param_list][1][0],
            'socket': param_list[place_1_in_param_list][1][1]
        }
        with open('server_state.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False)
        continue_game(1, 'не принят ответ', clients_sockets[1], clients_addresses[1])
    elif connected == 2:
        data = {}
        data['client1'] = {
            'status': 'не принят ответ',
            'address': param_list[place_1_in_param_list][1][0],
            'socket': param_list[place_1_in_param_list][1][1]
        }
        data['client0'] = {
            'status': 'не принят ответ',
            'address': param_list[place_0_in_param_list][1][0],
            'socket': param_list[place_0_in_param_list][1][1]
        }
        with open('server_state.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False)
        pass

    t1 = ThreadCloseSocket(hostSocket)
    t1.daemon = True
    t1.start()

    with concurrent.futures.ThreadPoolExecutor() as executor:
       futures = [executor.submit(clientThread, param) for param in param_list]

    a = {
        "камень": "ножницы",
        "ножницы": "бумага",
        "бумага": "камень"
    }

    b = answers[0]
    c = answers[1]

    if b == 'disconnected' and b != c:
        print('Один из игроков отключился, игра отменена')
        send_message(place_1_in_param_list, '\nСоперник не сделал ход')
        send_message(place_1_in_param_list, 'Соперник отключился, игра отменена')
    elif c == 'disconnected' and b != c:
        print('Один из игроков отключился, игра отменена')
        send_message(place_0_in_param_list, '\nСоперник не сделал ход')
        send_message(place_0_in_param_list, 'Соперник отключился, игра отменена')
    elif c == 'disconnected' and b == 'disconnected':
        print("Оба игрока отключились, игра отменена")
    else:
        print('Ход игрока 1:', b)
        print('Ход игрока 2:', c)

        send_message(place_0_in_param_list, '\nХод соперника: ' + c)
        send_message(place_1_in_param_list, '\nХод соперника: ' + b)

        if b == c:
            print("Ничья")
            send_message(place_0_in_param_list, 'Ничья')
            send_message(place_1_in_param_list, 'Ничья')
        for i, j in a.items():
            if b == i and c == j:
                print("Победил Игрок 1")
                send_message(place_0_in_param_list, 'Вы победили')
                send_message(place_1_in_param_list, 'Вы проиграли')
            elif c == i and b == j:
                print("Победил Игрок 2")
                send_message(place_0_in_param_list, 'Вы проиграли')
                send_message(place_1_in_param_list, 'Вы победили')

        for i in range(len(clients)):
            try:
                clients[i].close()
            except Exception as e:
                pass

    # удалить файл
    os.remove('server_state.json')

    hostSocket.close()
    sys.exit()

def continue_game_2_players_with_1_answer(client_num, client_answer, clients_sockets, clients_addresses):
    global answers
    global param_list
    global clients

    clients = list()

    hostSocket = socket(AF_INET, SOCK_STREAM)
    hostSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    hostSocket.settimeout(0.05)

    hostIp = "127.0.0.1"
    portNumber = 9090
    hostSocket.bind((hostIp, portNumber))
    hostSocket.listen()
    print("Waiting for connection...")

    param_list = list()

    answers = ['не принят ответ', 'не принят ответ']

    connected = -1  # -1 - никто не подключен, 0 - подключен 0, 1 - подключен 1, 2 - подключены все

    saved_socket = 0
    saved_address = 0

    place_0_in_param_list = -1
    place_1_in_param_list = -1

    tic = time.perf_counter()
    while time.perf_counter() - tic < 10:  # ждать определенное количество времени, а не всегда (случай когда клиент был, но отвалился) (done)
        try:
            clientSocket, clientAddress = hostSocket.accept()

            if clientAddress[1] == clients_sockets[1 - client_num] and clientAddress[0] == clients_addresses[1 - client_num]:
                saved_socket = clientSocket
                saved_address = clientAddress

            if connected != 0 and clientAddress[1] == clients_sockets[0] and clientAddress[0] == clients_addresses[0]:
                clients.append(clientSocket)
                param_list.append((clientSocket, clientAddress, 0))  # добавляем i=len(clients)-1 (done)
                place_0_in_param_list = len(param_list) - 1
                if connected == 1:
                    connected = 2
                    break
                else:
                    connected = 0
            if connected != 1 and clientAddress[1] == clients_sockets[1] and clientAddress[0] == clients_addresses[1]:
                clients.append(clientSocket)
                param_list.append((clientSocket, clientAddress, 1))  # добавляем i=len(clients)-1 (done)
                place_1_in_param_list = len(param_list) - 1
                if connected == 0:
                    connected = 2
                    break
                else:
                    connected = 1
            if not (clientAddress[1] == clients_sockets[0] and clientAddress[0] == clients_addresses[0] or clientAddress[1] == clients_sockets[1] and clientAddress[0] == clients_addresses[1]):
                clientSocket.send(json.dumps('С вами тут играть не хотят').encode("utf-8"))
                clientSocket.close()
        except Exception as e:
            pass

    if connected == -1:
        # все отключились, никто не выжил - написать конец проги (done)
        print('Все отключились, никто не выжил')
        os.remove('server_state.json')
        hostSocket.close()
        sys.exit()
    elif connected == 0:
        answers[1] = 'disconnected'
        continue_game(0, 'не принят ответ', clients_sockets[0], clients_addresses[0])
    elif connected == 1:
        answers[0] = 'disconnected'
        continue_game(1, 'не принят ответ', clients_sockets[1], clients_addresses[1])
    elif connected == 2:
        pass

    t1 = ThreadCloseSocket(hostSocket)
    t1.daemon = True
    t1.start()

    # client_num - тот кто ответил
    i = 1-client_num
    clientAddress = saved_address
    clientSocket = saved_socket

    try:
        clientSocket.send(json.dumps('Выберите камень / ножницы / бумага: ').encode("utf-8"))
        while True:
            answer = json.loads(clientSocket.recv(1024).decode("utf-8"))
            if answer == 'камень' or answer == 'ножницы' or answer == 'бумага':
                clientSocket.send(json.dumps('Ваш ход принят. Ждите пока соперник ответит').encode("utf-8"))
                break
            else:
                clientSocket.send(json.dumps(
                    'Ход ' + answer + ' не распознан. Введите один из вариантов: камень / ножницы / бумага').encode(
                    "utf-8"))
    except Exception as e:
        clients.remove(clientSocket)
        print(clientAddress[0] + ":" + str(clientAddress[1]) + " disconnected")
        answer = 'disconnected'
        clientSocket.close()
    answers[i] = answer
    answers[1-i] = client_answer

    a = {
        "камень": "ножницы",
        "ножницы": "бумага",
        "бумага": "камень"
    }

    b = answers[0]
    c = answers[1]

    if b == 'disconnected' and b != c:
        print('Один из игроков отключился, игра отменена')
        send_message(place_1_in_param_list, '\nСоперник не сделал ход')
        send_message(place_1_in_param_list, 'Соперник отключился, игра отменена')
    elif c == 'disconnected' and b != c:
        print('Один из игроков отключился, игра отменена')
        send_message(place_0_in_param_list, '\nСоперник не сделал ход')
        send_message(place_0_in_param_list, 'Соперник отключился, игра отменена')
    elif c == 'disconnected' and b == 'disconnected':
        print("Оба игрока отключились, игра отменена")
    else:
        print('Ход игрока 1:', b)
        print('Ход игрока 2:', c)

        send_message(place_0_in_param_list, '\nХод соперника: ' + c)
        send_message(place_1_in_param_list, '\nХод соперника: ' + b)

        if b == c:
            print("Ничья")
            send_message(place_0_in_param_list, 'Ничья')
            send_message(place_1_in_param_list, 'Ничья')
        for i, j in a.items():
            if b == i and c == j:
                print("Победил Игрок 1")
                send_message(place_0_in_param_list, 'Вы победили')
                send_message(place_1_in_param_list, 'Вы проиграли')
            elif c == i and b == j:
                print("Победил Игрок 2")
                send_message(place_0_in_param_list, 'Вы проиграли')
                send_message(place_1_in_param_list, 'Вы победили')

        for i in range(len(clients)):
            try:
                clients[i].close()
            except Exception as e:
                pass

    # удалить файл
    os.remove('server_state.json')

    hostSocket.close()
    sys.exit()


# json:
# ('disconnected', 'disconnected')
# ('не принят ответ', 'disconnected')
# ('disconnected', 'не принят ответ')
# ('не принят ответ', 'Не принят ответ')
# ('не принят ответ', ans)
# (ans, 'Не принят ответ')

if not os.path.isfile('server_state.json'):
    data = {}
    data['client1']={
        'status': 'disconnected'
    }
    data['client0']={
        'status': 'disconnected',
    }
    with open('server_state.json','w') as f:
        json.dump(data, f, ensure_ascii=False )

with open('server_state.json') as f:
    server_state = json.load(f)

validators = list()
for i in range(6):
    with open('schema_{}.json'.format(i), 'r', encoding="utf-8") as f:
        validators.append(Draft7Validator(json.load(f)))


if validators[0].is_valid(server_state):
   # print('validators[0]')
    new_game()
elif validators[1].is_valid(server_state):
    #print('validators[1]')
    ans = server_state['client0']['status']
    client_socket = server_state['client0']['socket']
    client_address = server_state['client0']['address']
    continue_game(0, ans, client_socket, client_address)
elif validators[2].is_valid(server_state):
    #print('validators[2]')
    ans = server_state['client1']['status']
    client_socket = server_state['client1']['socket']
    client_address = server_state['client1']['address']
    continue_game(1, ans, client_socket, client_address)
elif validators[3].is_valid(server_state):
    #print('validators[3]')
    client_socket0 = server_state['client0']['socket']
    client_address0 = server_state['client0']['address']

    client_socket1 = server_state['client1']['socket']
    client_address1 = server_state['client1']['address']
    continue_game_2_players_without_answers([client_socket0, client_socket1], [client_address0, client_address1])
elif validators[4].is_valid(server_state):
    #print('validators[4]')
    ans0 = server_state['client0']['status']
    client_socket0 = server_state['client0']['socket']
    client_address0 = server_state['client0']['address']

    ans1 = server_state['client1']['status']
    client_socket1 = server_state['client1']['socket']
    client_address1 = server_state['client1']['address']
    continue_game_2_players_with_1_answer(1, ans1, [client_socket0, client_socket1], [client_address0, client_address1])
elif validators[5].is_valid(server_state):
    #print('validators[5]')
    ans0 = server_state['client0']['status']
    client_socket0 = server_state['client0']['socket']
    client_address0 = server_state['client0']['address']

    ans1 = server_state['client1']['status']
    client_socket1 = server_state['client1']['socket']
    client_address1 = server_state['client1']['address']
    continue_game_2_players_with_1_answer(0, ans0, [client_socket0, client_socket1], [client_address0, client_address1])
else:

    data = {}
    data['client1']={
        'status': 'disconnected'
    }
    data['client0']={
        'status': 'disconnected',
    }
    with open('server_state.json','w') as f:
        json.dump(data, f, ensure_ascii=False )
    print("Предыдущее сохранение повреждено, начало новой игры")
    new_game()


# сервер запустился в первый раз
# проверяем, есть ли json
# нет -> создаем json ('disconnected', 'disconnected')
# проверяем содержимое
# 0 если ('disconnected', 'disconnected') - новая игра
# 1 если ('не принят ответ', 'disconnected') - доиграть игру с 0 игроком
# 2 если ('disconnected', 'не принят ответ') - доиграть игру с 1 игроком
# 3 если ('не принят ответ', 'не принят ответ') - продолжаем игру для конкретных игроков
# 4 если ('не принят ответ', ans) - продолжаем игру для 0 игрока, но с загруженным ответом для 1
# 5 если (ans, 'Не принят ответ') - продолжаем игру для 1 игрока, но с загруженным ответом для 0