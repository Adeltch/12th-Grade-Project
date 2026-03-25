__author__ = "Adel Tchernitsky"


import threading
from Graphics_Thread import handle_graphics
from Music.Music_Thread import do_music
from Communication_Thread import handle_communication
import sys
sys.path.append("..")
from Protocol.Socket import *


SERVER_ADDRESS = ("127.0.0.1", 1989)
WITH_MUSIC = False


def main():
    client_socket, connected = connect(SERVER_ADDRESS)
    if not connected:
        print(f"Error while trying to connect to {SERVER_ADDRESS}")
        return

    print(f"Connected to Server{SERVER_ADDRESS}")

    communication_thread = threading.Thread(target=handle_communication, args=(client_socket,))
    graphics_thread = threading.Thread(target=handle_graphics, args=())
    threads = [communication_thread, graphics_thread]

    if WITH_MUSIC:  # If True will create music thread as well
        music_thread = threading.Thread(target=do_music, args=())
        threads.append(music_thread)

    for thread in threads:  # Star all threads in client
        thread.start()

    for thread in threads:  # Wait for all threads in client to finish
        thread.join()

    print("program finished")


if __name__ == "__main__":
    main()
