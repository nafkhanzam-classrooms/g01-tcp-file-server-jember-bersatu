import socket
import select
import sys
from server_utils import (
    handle_list,
    receive_file,
    send_file,
    parse_message,
    broadcast,
    SERVER_FILES_DIR,
    BUFFER_SIZE,
)

HOST = "127.0.0.1"
PORT = 9090

if sys.platform == "win32":
    print("[ERROR] server-poll.py tidak didukung di Windows. Gunakan server-select.py.")
    sys.exit(1)


def handle_message(conn, addr, clients):
    """Proses satu pesan dari client yang siap dibaca, dipanggil saat pollin event terjadi."""
    try:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            raise ConnectionResetError("Client kirim EOF")

        cmd, args = parse_message(data)

        if cmd == "LIST":
            conn.sendall(handle_list())

        elif cmd == "UPLOAD":
            filename = args["filename"]
            filesize = args["filesize"]
            received = receive_file(conn, filename, filesize)
            print(f"[UPLOAD] {filename} ({received} bytes) dari {addr}")
            broadcast(clients, addr, f"upload '{filename}' ke server.")

        elif cmd == "DOWNLOAD":
            filename = args["filename"]
            ok = send_file(conn, filename)
            if ok:
                print(f"[DOWNLOAD] {filename} dikirim ke {addr}")

        elif cmd == "MSG":
            text = args["text"]
            print(f"[MSG dari {addr}]: {text}")
            broadcast(clients, addr, text)

        else:
            conn.sendall(b"ERROR|Perintah tidak dikenal.")

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
        return False
    return True


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(50)
    print(f"[SERVER-POLL] Berjalan di {HOST}:{PORT}")
    print(
        "[SERVER-POLL] Mode: POLL syscall — I/O multiplexing tanpa batas FD, Linux/macOS only\n"
    )

    poller = select.poll()

    poller.register(server.fileno(), select.POLLIN)

    fd_to_socket = {server.fileno(): server}
    clients = {}

    try:
        while True:
            events = poller.poll(-1)

            for fd, event in events:
                sock = fd_to_socket[fd]

                if event & select.POLLIN:
                    if sock is server:
                        conn, addr = server.accept()
                        print(f"[+] Client baru: {addr}")
                        clients[conn] = addr
                        fd_to_socket[conn.fileno()] = conn
                        poller.register(conn.fileno(), select.POLLIN)

                    else:
                        addr = clients.get(sock, ("?", "?"))
                        ok = handle_message(sock, addr, clients)

                        if not ok:
                            poller.unregister(fd)
                            del fd_to_socket[fd]
                            clients.pop(sock, None)
                            sock.close()
                            print(f"[-] Client terputus: {addr}")

                elif event & (select.POLLHUP | select.POLLERR):
                    addr = clients.get(sock, ("?", "?"))
                    print(f"[-] Client disconnect/error: {addr}")
                    poller.unregister(fd)
                    del fd_to_socket[fd]
                    clients.pop(sock, None)
                    sock.close()

    except KeyboardInterrupt:
        print("\n[INFO] Server dihentikan.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
