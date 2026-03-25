__author__ = "Adel Tchernitsky"


from Socket import *
import threading


BIND_ADDRESS = ("0.0.0.0", 1989)
LISTEN = 5
ACCEPT_TIMEOUT = 1


finish = False


def create_message():
    return input("What to send client> ")


def handle_message(message):
    print(f"Client sent> {message}")


def handle_client(client_socket):
    while not finish:
        response = create_message()
        if not send(client_socket, response):  # In case server disconnected everything will finish
            update_global(Globals.status, PlayerStatus.Finish)
            break

        try:
            succeeded, message = recv(client_socket)
            if not succeeded:  # In case server disconnected everything will finish
                update_global(Globals.status, PlayerStatus.Finish)
                break

            handle_message(message)
        except SOCKET_TIMEOUT_EXCEPTION:
            pass
        except EOFError:
            break


def main():
    global finish

    server_sock = create_server_socket(BIND_ADDRESS, LISTEN)  # Create server socket
    if not server_sock:
        print("Port already occupied!")
        return
    set_timeout(server_sock, ACCEPT_TIMEOUT)

    threads = []
    while not finish:
        try:
            try:
                client_sock, address = server_sock.accept()
            except SOCKET_TIMEOUT_EXCEPTION:
                continue

            t = threading.Thread(target=handle_client, args=(client_sock, ))  # Create new thread for client
            t.start()
            threads.append(t)  # Add thread to threads list

        except KeyboardInterrupt:
            finish = True

    print("Waiting for all players to finish the game...")
    for t in threads:
        t.join()
    print("all threads finished")

    close(server_sock)
    print("Server finished!")


if __name__ == "__main__":
    main()
