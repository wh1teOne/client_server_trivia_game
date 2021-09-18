import socket
import chatlib  # protocol functions
import random  # For random questions asked
import select  # For enabling multiple connections of clients to server
import requests  # For pulling random questions from the internet
import json  # For handling the JSON requests received.

# to be added: 1. handle 2 answers wrong answers problem. 2. adding already used questions to list. 3. provide no_answers response.

users_information_dict = dict()
questions = dict()
peer_name_tuple = tuple()
logged_users_dict = dict()
ERROR_MSG = 'Error! '
SERVER_PORT = 5631
SERVER_IP = '127.0.0.1'
messages_to_send = list()
MSG_MAX_LENGTH = 1024
QUESTIONS_AMOUNT = 2


def add_answered_question_to_user(user, question_id):
    """
    gets username and question id and adds it to the users dictionary (to avoid repetitive answers).
    :param user: username.
    :param question_id: question's id.
    :return: None.
    """
    global users_information_dict
    users_information_dict[user]['questions_asked'].append(question_id)


def build_and_send_message(conn, cmd, data):
    """
    :param conn: client socket to which we want to send the message.
    :param cmd: the command to send according to the trivia protocol.
    :param data: the message to send.
    :return: None.
    """
    try:
        data_to_send = chatlib.build_message(cmd, data).encode()
        conn.send(data_to_send)
        print('[SERVER]', data_to_send.decode())  # Debug print
        messages_to_send.append((conn.getpeername(), data_to_send))
    except:
        messages_to_send.append((conn.getpeername(), ERROR_MSG))


def recv_message_and_parse(conn):
    """
    :param conn: client socket from which we receive & parse the message.
    :return: cmd - protocol command received from client, data - message information from client.
    """
    try:
        received_msg = conn.recv(1024).decode()
        cmd, data = chatlib.parse_message(received_msg)
        print('[CLIENT]', cmd, data)  # debug print
        return cmd, data
    except:
        return None, None


def load_questions():
    """
    Loads questions bank from file questions API.
    Recieves: None.
    Returns: questions dictionary
    """
    res = requests.get(f'https://opentdb.com/api.php?amount={QUESTIONS_AMOUNT}&difficulty=easy')
    json_res = res.text
    loaded = json.loads(json_res)
    question_dict = {}
    question_num = 1
    for question in loaded['results']:
        correct_answer = question['correct_answer']
        incorrect_answers = question['incorrect_answers']
        incorrect_answers.append(correct_answer)
        random.shuffle(incorrect_answers)
        correct_answer_updated_position = incorrect_answers.index(correct_answer)
        question_dict[question_num] = {'question': question['question'], 'answers': incorrect_answers,
                                       'correct': correct_answer_updated_position + 1}
        question_num += 1
    return question_dict


def fix_url_encoded_questions(string_question):

    """
    takes the string input and replaces url encoded letters to normal format.
    :param string_question: the question string that we want to fix
    :return: fixed question string

    """
    to_switch_dict = {'&#039;': "'",
                      '&quot;': '"',
                      '&amp;': '&'}
    for i in to_switch_dict.keys():
        print(to_switch_dict[i])
        string_question = string_question.replace(i, to_switch_dict[i])
    return string_question


def load_user_database():
    """
    Loads the user database.
    :return: user dictionary.
    """
    quiz_users = {
        'test'	:	{'password': 'test', 'score': 0, 'questions_asked': []},
        'yossi'		:	{'password': '123', 'score': 0, 'questions_asked': []},
        'master'	:	{'password': 'master', 'score': 0, 'questions_asked': []}
    }
    return quiz_users


def setup_socket():
    """
    creates new listening socket and returns it.
    :return: the socket object.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((SERVER_IP, SERVER_PORT))
        sock.listen()
        print('Server is listening...')
        return sock
    except OSError:
        print(f'{ERROR_MSG} adress already in use.')


def send_error(conn, error_msg):
    """
    send error message with given message
    :param conn: client socket.
    :param error_msg: error message to be passed through client socket.
    :return:
    """
    conn.send(error_msg.encode())


def handle_getscore_message(conn, username):
    """
    receives the client socket and username of that socket and returns a YOUR_SCORE message.
    :param conn: client socket object.
    :param username: the username of the client socket.
    :return: None.
    """
    global users_information_dict
    user_score_to_send = users_information_dict[username]['score']
    print(user_score_to_send)
    build_and_send_message(conn, 'YOUR_SCORE', f'{user_score_to_send}')


def handle_highscore_message(conn):
    """
    recieves client socket to which the highscore of current time is sent with the build_and_send_message function.
    :param conn: client socket object.
    :return: None.
    """
    global users_information_dict
    user_list = list()
    for name, data in users_information_dict.items():
        tmp = {
            'name': name,
            'score': data['score']
        }
        user_list.append(tmp)
    sorted_users = sorted(user_list, key=lambda k: k['score'], reverse=True)
    build_and_send_message(conn, 'ALL_SCORE', f"{sorted_users[0]['name']} : {sorted_users[0]['score']}\n{sorted_users[1]['name']} : {sorted_users[1]['score']}\n{sorted_users[2]['name']} : {sorted_users[2]['score']}")


def handle_logged_message(conn):
    """
    receives client socket to which a list of logged users_information_dict in current time is passed.
    :param conn: client socket object.
    :return:None.
    """
    global logged_users_dict
    try:
        msg_to_send = str()
        for i in logged_users_dict:
            msg_to_send += f'{logged_users_dict[i]}\n'
        build_and_send_message(conn, 'LOGGED_ANSWER', msg_to_send)
    except:
        send_error(conn, ERROR_MSG)


def handle_logout_message(conn):
    """
    Removes the client socket from the logged users_information_dict dictionary
    :param conn:
    :return:None.
    """
    global logged_users_dict
    logged_users_dict.pop(conn.getpeername())
    print(f' logged user list: {logged_users_dict}')


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users_dict.
    :param conn: client socket object.
    :param data: client socket message.
    :return: None.
    """
    global users_information_dict  # This is needed to access the same users_information_dict dictionary from all functions
    global logged_users_dict	 # To be used later
    login_cred = chatlib.split_data(data, 1)
    if login_cred[0] in users_information_dict:
        if login_cred[1] == users_information_dict[login_cred[0]]['password']:
            build_and_send_message(conn, 'LOGIN_OK', '')
            logged_users_dict[conn.getpeername()] = login_cred[0]
            print(f' logged user list: {logged_users_dict}')
        else:
            build_and_send_message(conn, 'ERROR', 'Wrong password.')
    else:
        build_and_send_message(conn, 'ERROR', 'User does not exist.')


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command.
    :param conn: client socket object.
    :param cmd: client socket command
    :param data: client message.
    :return: None
    """
    global logged_users_dict
    if cmd == 'LOGIN':
        handle_login_message(conn, data)
    elif cmd == 'LOGOUT' or cmd is None:
        handle_logout_message(conn)
    elif cmd == 'MY_SCORE':
        handle_getscore_message(conn, logged_users_dict[conn.getpeername()])
    elif cmd == 'HIGHSCORE':
        handle_highscore_message(conn)
    elif cmd == 'LOGGED':
        handle_logged_message(conn)
    elif cmd == 'GET_QUESTION':
        handle_question_message(conn)
    elif cmd == 'SEND_ANSWER':
        handle_answer_message(conn, logged_users_dict[conn.getpeername()], data)
    else:
        build_and_send_message(conn, 'ERROR', 'Error! command does not exist.')


def create_random_question():
    """
    :return: random question string to be forwarded to the client
    """
    global questions
    answers_string = str()
    random_question_tuple = random.choice(list(questions.items()))
    for i in random_question_tuple[1]['answers']:
        answers_string = answers_string + "#" + i
    final_string = str(random_question_tuple[0]) + "#" + random_question_tuple[1]['question'] + answers_string
    final_string = fix_url_encoded_questions(final_string)
    return final_string


def handle_question_message(conn):
    """
    sends the user a random question. made with the create_random_question function.
    :param conn: client socket.
    :return: None.
    """
    global questions
    global users_information_dict
    global logged_users_dict
    if len(users_information_dict[logged_users_dict[conn.getpeername()]]['questions_asked']) == QUESTIONS_AMOUNT:
        build_and_send_message(conn, 'NO_QUESTIONS', '')
    else:
        question_for_client = create_random_question()
        build_and_send_message(conn, 'YOUR_QUESTION', question_for_client)


def handle_answer_message(conn, username, data):
    """
    :param conn: client socket.
    :param username: client username.
    :param data: client answer.

    the function checks if the client answer is correct. if so, add points to the username.
    either way sends a message whether answer is correct or not.
    :return:
    none
    """
    global users_information_dict
    global questions
    acceptable_answer = ['1', '2', '3', '4']
    question_id, choice = chatlib.split_data(data, 1)
    while choice not in acceptable_answer:
        build_and_send_message(conn, 'UNACCEPTABLE_ANSWER', '')
        new_cmd, new_data = recv_message_and_parse(conn)
        question_id, choice = chatlib.split_data(new_data, 1)
        if int(choice) == int(questions[int(question_id)]['correct']):
            build_and_send_message(conn, 'CORRECT_ANSWER', '')
            users_information_dict[username]['score'] += 5
            add_answered_question_to_user(username, question_id)
            return
        else:
            build_and_send_message(conn, 'WRONG_ANSWER', '')
            add_answered_question_to_user(username, question_id)
            return
    if int(choice) == int(questions[int(question_id)]['correct']):
        build_and_send_message(conn, 'CORRECT_ANSWER', '')
        users_information_dict[username]['score'] += 5
        add_answered_question_to_user(username, question_id)
    else:
        build_and_send_message(conn, 'WRONG_ANSWER', '')
        add_answered_question_to_user(username, question_id)


def print_client_sockets(socket_dict):
    """
    prints out the client connected to the server based on IP and port.
    :param socket_dict: the dictionary of client connected to the server.
    """
    global logged_users_dict
    print('CONNECTED CLIENT SOCKETS:')
    for ip, port in socket_dict.keys():
        print(f'IP: {ip}, PORT: {port}')


def main():

    global users_information_dict
    global questions
    global peer_name_tuple
    global messages_to_send
    users_information_dict = load_user_database()
    questions = load_questions()
    client_sockets = list()
    print('Welcome to Trivia Server!')
    server_socket = setup_socket()
    print('[SERVER] Listening for new clients...')
    while True:
        try:
            ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])
            for current_socket in ready_to_read:
                if current_socket is server_socket:
                    (client_socket, client_address) = server_socket.accept()
                    print(f'[SERVER] New client has joined the server: {client_address}')
                    client_sockets.append(client_socket)
                    print_client_sockets(logged_users_dict)
                else:
                    try:
                        print('New data from client')
                        cmd, data = recv_message_and_parse(current_socket)
                        peer_name_tuple = current_socket.getpeername()
                        handle_client_message(current_socket, cmd, data)
                        for message in messages_to_send:
                            current_socket, data = message
                            if current_socket in ready_to_write:
                                current_socket.send(data.encode())
                                messages_to_send.remove(message)
                            else:
                                pass
                    except:
                        client_sockets.remove(current_socket)
                        print('[SERVER] Client socket closed.')
                        break
        except TypeError:
            print(f'{ERROR_MSG} socket already open.')
            break


if __name__ == '__main__':
    main()
