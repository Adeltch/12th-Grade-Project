# CTF1:
# stage2
def xor_strings(plaintext, key):
    ciphertext = []
    key_length = len(key)

    for i, char in enumerate(plaintext):
        # Convert chars to ints, XOR, then store
        xor_char = ord(char) ^ ord(key[i % key_length])
        ciphertext.append(xor_char)

    return bytes(ciphertext)  # Return as bytes


my_str = "Great! I see you know how to xor"
key = "hello"

ciphered = xor_strings(my_str, key)
print(ciphered.hex())


# stage4
def vigenere_encrypt(plaintext, key):
    ciphertext = ""
    key = key.upper()
    key_length = len(key)

    for i, char in enumerate(plaintext):
        if char.isalpha():
            p = ord(char.upper()) - ord('A')
            k = ord(key[i % key_length]) - ord('A')
            c = (p + k) % 26
            ciphertext += chr(c + ord('A'))
        else:
            ciphertext += char
    return ciphertext


def vigenere_decrypt(ciphertext, key):
    plaintext = ""
    key_length = len(key)
    key = key.upper()

    for i, char in enumerate(ciphertext):
        if char.isalpha():  # Only decrypt letters
            # Convert char and key to 0-25
            c = ord(char.upper()) - ord('A')
            k = ord(key[i % key_length]) - ord('A')

            # Decrypt
            p = (c - k) % 26
            plaintext += chr(p + ord('A'))
        else:
            plaintext += char  # Keep non-letters as-is

    return plaintext


# Extra code for project:
# For communication thread, making create_response shorter:
def handle_finish(_):
    return Exit()


def handle_get_username(_):
    return Login(handle_user_name_input())


def handle_choose_ctf(message):
    return CTFChoice(handle_ctf_choice(message))


def handle_in_game(message):
    current_answer = get_answer(message)
    if current_answer == "hint":
        return HintRequest()
    return Answer(current_answer)


def handle_show_states(message):
    show_message_content(message)
    if status == PlayerStatus.ShowFinalScore:
        return Exit()
    return None


RESPONSE_HANDLERS = {PlayerStatus.Finish: handle_finish, PlayerStatus.GetUserName: handle_get_username,
                     PlayerStatus.ChooseCTF: handle_choose_ctf, PlayerStatus.InGame: handle_in_game,
                     PlayerStatus.ShowResponse: handle_show_states, PlayerStatus.ShowFinalScore: handle_show_states,
                     PlayerStatus.ShowError: handle_show_states}


def create_response(message):
    print(f"\nCurrent status is: {status}")

    handler = RESPONSE_HANDLERS.get(status)
    if handler:
        return handler(message)