import socket
import chatlib

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5631

# HELPER SOCKET METHODS


def build_and_send_message(conn, cmd, data):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    :param conn: server socket object
    :param cmd: command to be sent to server.
    :param data: data message to send.
    :return: None.
    """
    data_to_send = chatlib.build_message(cmd, data).encode()
    conn.send(data_to_send)


def recv_message_and_parse(conn):
    """
    receives a new message from given socket,
    then parses the message using chatlib.
    If error occures, will return None, None
    :param conn: server socket object.
    :return: None.
    """
    try:
        received_msg = conn.recv(1024).decode()
        cmd, data = chatlib.parse_message(received_msg)
        return cmd, data
    except:
        return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN


def connect():
    """
    creates and returns a socket object that is connected to the trivia server.
    :return: client socket.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    print('Connection established to server.\n')
    return client_socket


def error_and_exit(error_msg):
    """
    incase of an error, prints out an error message and closes the program.
    :param error_msg: error message that will be printed from the server.
    :return: None.
    """
    print(f'the error: {error_msg} was received...\n exiting client')
    exit()


def login(conn):
    """
    prompts the user to enter username and password, and sends the message to the server.
    while cmd is not login ok, keeps asking for it.
    :param conn: server socket object.
    :return: None.
    """
    cmd = ''
    while cmd != 'LOGIN_OK':
        username = input('Please enter username: \n')
        password = input('Please enter the password \n')
        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT['login_msg'], f'{username}#{password}')
        cmd, data = recv_message_and_parse(conn)
        print(f'{data}')
    print('Logged in.\n')


def logout(conn):
    """
    send the server logout message.
    :param conn: server socket object.
    :return: None.
    """
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT['logout_msg'], '')
    print('Logging out...\n')


def build_send_recv_parse(conn, cmd, data):
    """
    :param conn: server socket object.
    :param cmd: command message to be sent to server.
    :param data: data to be sent to server.
    :return: the command message receieved from the server (msg_code) and data of that message (srv_data)
    """
    """Receives socket, command and data , use the send and receive functions,
    and eventually return the server answer in data and msg code"""
    build_and_send_message(conn, cmd, data)
    msg_code, srv_data = recv_message_and_parse(conn)
    return msg_code, srv_data


def get_score(conn):
    """
    receives server socket, sends a get_score message, receives server response and prints it out.
    for any error received, prints it out.
    :param conn: server socket object.
    :return: None.
    """
    try:
        cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT['my_score_msg'], '')
        print(f'Your score is: {data}\n')
    except:
        error_and_exit(chatlib.ERROR_RETURN)


def get_highscore(conn):
    """
    receives a server socket socket, prints out the highscore table as received from the server.
    :param conn: server socket object.
    :return: None.
    """
    try:
        cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT['highscore_msg'], '')
        print(f'The highscore table is:\n{data}\n')
    except:
        error_and_exit(chatlib.ERROR_RETURN)


def play_question(conn):
    """
    receives a server socket as arg. requests a question from the server. splits received response to 2/4 answers.
    for any error received, prints out error message and returns to server a None response.
    :param conn: server socket object.
    :return: None.
    """

    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT['get_question_msg'], '')
    try:
        if cmd == 'NO_QUESTIONS':
            print('There are no more questions to ask. game over.')
            return
        else:
            question_list = chatlib.split_data(data, 5)
            user_answer = input(f'{question_list[1]}:\n1. {question_list[2]}\n2. {question_list[3]}\n3. {question_list[4]}\n4. {question_list[5]}\n')
            answer_cmd, answer_data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT['send_answer_msg'],
                                                            f'{question_list[0]}#{user_answer}')
            try:
                while answer_cmd == 'UNACCEPTABLE_ANSWER':
                    new_answer = input('Please enter a valid answer (numbers) as options available.\n')
                    answer_cmd, answer_data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT['send_answer_msg'],
                                           f'{question_list[0]}#{new_answer}')
                if answer_cmd == 'CORRECT_ANSWER':
                    print('The answer you provided is correct!')
                elif answer_cmd == 'WRONG_ANSWER':
                    print(f'the answer you provided is wrong.')
            except:
                error_and_exit(chatlib.ERROR_RETURN)
    except TypeError:
        question_list = chatlib.split_data(data, 3)
        user_answer = input(f'{question_list[1]}:\n1. {question_list[2]}\n2. {question_list[3]}\n')
        answer_cmd, answer_data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT['send_answer_msg'],
                                                        f'{question_list[0]}#{user_answer}')
        try:
            if answer_cmd == 'CORRECT_ANSWER':
                print('The answer you provided is correct!')
            elif answer_cmd == 'WRONG_ANSWER':
                print(f'the answer you provided is wrong.')
            while answer_cmd == 'UNACCEPTABLE_ANSWER':
                new_answer = input('Please enter a valid answer (numbers) as options available.\n')
                answer_cmd, answer_data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT['send_answer_msg'],
                                       f'{question_list[0]}#{new_answer}')
                try:
                    if answer_cmd == 'CORRECT_ANSWER':
                        print('The answer you provided is correct!')
                    elif answer_cmd == 'WRONG_ANSWER':
                        print(f'the answer you provided is wrong.')
                    elif answer_cmd == 'NO_QUESTIONS':
                        print('There are no more questions to ask. game over.')
                except:
                    error_and_exit(chatlib.ERROR_RETURN)
        except:
            error_and_exit(chatlib.ERROR_RETURN)


def get_logged_users(conn):
    """
    receives a server socket object and prints out the users_information_dict' list currently connected.
    :param conn: server socket object.
    :return:
    """
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT['logged_answer_msg'], '')
    print(f'Connected users_information_dict at this time:\n {data}')


def main():
    client_socket = connect()
    login(client_socket)
    user_choice = ''
    while user_choice != 'q':
        user_choice = input('-----------------------------\nplease enter one of the above:\n'
                            'p        Play a trivia question\ns        Get my score\nh        Get high score\n'
                            'q        Quit\nl        Get current logged users\n-----------------------------\n')
        if user_choice not in ['s', 'h', 'q', 'p', 'l']:
            user_choice = input('-----------------------------\nplease enter one of the above:\n'
                                'p        Play a trivia question\ns        Get my score\nh        Get high score\n'
                                'q        Quit\nl        Get current logged users\n-----------------------------\n')
        if user_choice == 'h':
            get_highscore(client_socket)
        elif user_choice == 's':
            get_score(client_socket)
        elif user_choice == 'p':
            play_question(client_socket)
        elif user_choice == 'l':
            get_logged_users(client_socket)
    logout(client_socket)


if __name__ == '__main__':
    main()
