import socket
import threading
from server_utils import (
    handle_list, receive_file, send_file,
    parse_message, broadcast, SERVER_FILES_DIR, BUFFER_SIZE
)

HOST = '127.0.0.1'
PORT = 9090

clients_lock = threading.Lock()
clients = {}  


def handle_client(conn, addr):
    """
    Fungsi yang dijalankan di thread masing-masing client.
    Berjalan secara paralel dengan thread client lain.
    """
    print(f"[+] Thread baru untuk: {addr} (Thread: {threading.current_thread().name})")
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
                with clients_lock:
                    broadcast(clients, addr, f"upload '{filename}' ke server.")

            elif cmd == 'DOWNLOAD':
                filename = args['filename']
                ok = send_file(conn, filename)
                if ok:
                    print(f"[DOWNLOAD] {filename} dikirim ke {addr}")

            elif cmd == 'MSG':
                text = args['text']
                print(f"[MSG dari {addr}]: {text}")
                with clients_lock:
                    broadcast(clients, addr, text)

            else:
                conn.sendall(b"ERROR|Perintah tidak dikenal.")

    except Exception as e:
        print(f"[ERROR] Thread {addr}: {e}")
    finally:
        with clients_lock:
            clients.pop(conn, None)
        conn.close()
        print(f"[-] Thread selesai, client terputus: {addr}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(50)
    print(f"[SERVER-THREAD] Berjalan di {HOST}:{PORT}")
    print("[SERVER-THREAD] Mode: THREADING — 1 thread per client, berjalan paralel\n")

    try:
        while True:
            conn, addr = server.accept()

            with clients_lock:
                clients[conn] = addr

            t = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                name=f"Client-{addr[1]}", 
                daemon=True 
            )
            t.start()
            print(f"[INFO] Total thread aktif: {threading.active_count() - 1} client(s)")

    except KeyboardInterrupt:
        print("\n[INFO] Server dihentikan.")
    finally:
        server.close()


if __name__ == '__main__':
    main()