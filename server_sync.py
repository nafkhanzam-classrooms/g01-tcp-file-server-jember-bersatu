import socket
from server_utils import (
    handle_list, receive_file, send_file,
    parse_message, broadcast, SERVER_FILES_DIR, BUFFER_SIZE
)

HOST = '127.0.0.1'
PORT = 9090


def handle_client(conn, addr, all_clients):
    """Tangani satu sesi client secara penuh sebelum kembali ke loop utama."""
    print(f"[+] Client terhubung: {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break   

            cmd, args = parse_message(data)

            if cmd == 'LIST':
                conn.sendall(handle_list())

            elif cmd == 'UPLOAD':
                filename = args['filename']
                filesize = args['filesize']
                received = receive_file(conn, filename, filesize)
                print(f"[UPLOAD] {filename} ({received} bytes) dari {addr}")
                broadcast(all_clients, addr, f"upload '{filename}' ke server.")

            elif cmd == 'DOWNLOAD':
                filename = args['filename']
                ok = send_file(conn, filename)
                if ok:
                    print(f"[DOWNLOAD] {filename} dikirim ke {addr}")

            elif cmd == 'MSG':
                text = args['text']
                print(f"[MSG dari {addr}]: {text}")
                broadcast(all_clients, addr, text)

            else:
                conn.sendall(b"ERROR|Perintah tidak dikenal.")

    except Exception as e:
        print(f"[ERROR] Sesi {addr}: {e}")
    finally:
        conn.close()
        all_clients.pop(conn, None)
        print(f"[-] Client terputus: {addr}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVER-SYNC] Berjalan di {HOST}:{PORT}")
    print("[SERVER-SYNC] Mode: SYNCHRONOUS — hanya 1 client aktif dalam satu waktu\n")

    all_clients = {}  # {conn: addr}

    try:
        while True:
            conn, addr = server.accept()
            all_clients[conn] = addr
            handle_client(conn, addr, all_clients)
    except KeyboardInterrupt:
        print("\n[INFO] Server dihentikan.")
    finally:
        server.close()


if __name__ == '__main__':
    main()