# Protocol Constants
CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message
ACCEPTABLE_COMMANDS = ['LOGIN', 'LOGOUT', 'LOGGED', 'GET_QUESTION', 'SEND_ANSWER', 'MY_SCORE', 'HIGHSCORE', 'LOGIN_OK',
                       'LOGGED_ANSWER', 'YOUR_QUESTION', 'CORRECT_ANSWER', 'WRONG_ANSWER', 'UNACCEPTABLE_ANSWER',
                       'YOUR_SCORE', 'ALL_SCORE', 'ERROR', 'NO_QUESTIONS']

# Protocol Messages

PROTOCOL_CLIENT = {
    'login_msg': 'LOGIN',
    'logout_msg': 'LOGOUT',
    'my_score_msg': 'MY_SCORE',
    'highscore_msg': 'HIGHSCORE',
    'get_question_msg': 'GET_QUESTION',
    'logged_answer_msg': 'LOGGED',
    'send_answer_msg': 'SEND_ANSWER'
}
PROTOCOL_SERVER = {
    'login_ok_msg': 'LOGIN_OK',
    'login_failed_msg': 'ERROR'
}

# Other constants
ERROR_RETURN = None  # What is returned in case of an error
################################################################################################


def build_message(cmd, data):
    """
    Gets command name (str) and data field (str) and creates a valid protocol message
    Returns: str, or None if error occured.
    :param cmd: command name.
    :param data: data of the command.
    :return: protocol message.
    """
    if cmd not in ACCEPTABLE_COMMANDS:
        return ERROR_RETURN
    else:
        cmd_temp = cmd + ' '*(16 - len(cmd))  #checking cmd length to assemble cmd with rest spaces up to length of 16 bits.
        message = f'{cmd_temp}|{(4-len(str(len(data)))) * "0"}{len(data)}|{data}'#calculate data length to insert to the middle part of the message.
        return message


def parse_message(data):
    """
    Parses protocol message and returns command name and data field
    Returns: cmd (str), data (str). If some error occured, returns None, None
    :param data: data message
    :return: command and data.
    """
    try:
        cmd, msg_len, msg = data.split("|")
        stripped_cmd = cmd.strip()
        stripped_msg_len = msg_len.strip()
        if int(stripped_msg_len) == len(msg) and stripped_cmd in ACCEPTABLE_COMMANDS:
            return stripped_cmd, msg
        else:
            return ERROR_RETURN, ERROR_RETURN
    except:
        return ERROR_RETURN, ERROR_RETURN


def split_data(msg, expected_fields):
    """
     Helper method. gets a string and number of expected fields in it. Splits the string
    using protocol's data field delimiter (|#) and validates that there are correct number of fields.
    Returns: list of fields if all ok. If some error occured, returns None
    :param msg: message received.
    :param expected_fields: amount of | or # in the message to be expected.
    :return:
    """
    found_fields = int()
    for letter in msg:
        if letter == "#":
            found_fields += 1
    if expected_fields == found_fields:
        fields_to_return = msg.split('#')
        return fields_to_return
    else:
        return ERROR_RETURN


def join_data(msg_fields):
    """
    Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter.
    Returns: string that looks like cell1#cell2#cell3
    :param msg_fields: list of strings to be joined.
    :return: one string with data delimiters between list values.
    """
    string_to_return = str()
    for i in msg_fields:
        string_to_return = string_to_return + "#" + str(i)
    string_to_return = (string_to_return[1:])
    return string_to_return
