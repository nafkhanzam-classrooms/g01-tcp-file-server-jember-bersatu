import socket
import select
from server_utils import (
    handle_list, receive_file, send_file,
    parse_message, broadcast, SERVER_FILES_DIR, BUFFER_SIZE
)

HOST = '127.0.0.1'
PORT = 9090


def handle_message(conn, addr, clients):
    """Proses satu pesan dari client yang sudah siap dibaca."""
    try:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            raise ConnectionResetError("Client kirim EOF")

        cmd, args = parse_message(data)

        if cmd == 'LIST':
            conn.sendall(handle_list())

        elif cmd == 'UPLOAD':
            filename = args['filename']
            filesize = args['filesize']
            received = receive_file(conn, filename, filesize)
            print(f"[UPLOAD] {filename} ({received} bytes) dari {addr}")
            broadcast(clients, addr, f"upload '{filename}' ke server.")

        elif cmd == 'DOWNLOAD':
            filename = args['filename']
            ok = send_file(conn, filename)
            if ok:
                print(f"[DOWNLOAD] {filename} dikirim ke {addr}")

        elif cmd == 'MSG':
            text = args['text']
            print(f"[MSG dari {addr}]: {text}")
            broadcast(clients, addr, text)

        else:
            conn.sendall(b"ERROR|Perintah tidak dikenal.")

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
        conn.close()
        clients.pop(conn, None)


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(50)
    print(f"[SERVER-SELECT] Berjalan di {HOST}:{PORT}")
    print("[SERVER-SELECT] Mode: SELECT — I/O multiplexing, single-thread\n")

    clients = {}
    inputs = [server]   

    try:
        while True:
            readable, _, _ = select.select(inputs, [], [], 1.0)

            for sock in readable:
                if sock is server:
                    # Ada koneksi baru
                    conn, addr = server.accept()
                    print(f"[+] Client baru: {addr}")
                    clients[conn] = addr
                    inputs.append(conn)  
                else:
                    addr = clients.get(sock, ('?', '?'))
                    handle_message(sock, addr, clients)
                    if sock not in clients:
                        inputs.remove(sock)
                        print(f"[-] Client terputus: {addr}")

    except KeyboardInterrupt:
        print("\n[INFO] Server dihentikan.")
    finally:
        server.close()


if __name__ == '__main__':
    main()