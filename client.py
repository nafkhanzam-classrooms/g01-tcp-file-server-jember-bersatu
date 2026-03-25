import socket
import os
import threading
import time 

HOST = '127.0.0.1'
PORT = 9090
CLIENT_FILES_DIR = 'client_files'

os.makedirs(CLIENT_FILES_DIR, exist_ok=True)

BUFFER_SIZE = 4096

is_transferring = threading.Event()


def receive_messages(sock):
    """Thread listener — berhenti sementara saat transfer file berlangsung."""
    while True:
        try:
            if is_transferring.is_set():
                continue

            sock.settimeout(0.1)
            try:
                data = sock.recv(BUFFER_SIZE)
            except socket.timeout:
                continue

            if not data:
                print("\n[INFO] Koneksi ke server terputus.")
                os._exit(0)

            print(f"\n[SERVER] {data.decode(errors='replace')}")
            print(">> ", end='', flush=True)

        except Exception as e:
            if not is_transferring.is_set():
                print(f"\n[ERROR] Koneksi terputus: {e}")
                os._exit(0)


def send_file(sock, filename):
    filepath = os.path.join(CLIENT_FILES_DIR, filename)
    if not os.path.isfile(filepath):
        print(f"[ERROR] File '{filename}' tidak ditemukan di folder '{CLIENT_FILES_DIR}/'")
        return

    filesize = os.path.getsize(filepath)
    header = f"UPLOAD|{filename}|{filesize}"

    is_transferring.set()
    try:
        sock.sendall(header.encode())
        ack = sock.recv(BUFFER_SIZE)
        if ack != b"READY":
            print("[ERROR] Server tidak siap menerima file.")
            return

        sent = 0
        with open(filepath, 'rb') as f:
            while sent < filesize:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                sock.sendall(chunk)
                sent += len(chunk)

        print(f"[INFO] File '{filename}' ({filesize} bytes) berhasil dikirim ke server.")
    finally:
        is_transferring.clear()  


def download_file(sock, filename):
    is_transferring.set()
    time.sleep(0.1)  
    try:
        sock.sendall(f"DOWNLOAD|{filename}".encode())
        sock.settimeout(5)
        header = sock.recv(BUFFER_SIZE).decode(errors='replace')
        sock.settimeout(None)

        if header.startswith("ERROR"):
            print(f"[ERROR] {header.split('|', 1)[1]}")
            return

        parts = header.split('|')
        if parts[0] != "OK" or len(parts) < 2:
            print(f"[ERROR] Respons tidak dikenal: {header}")
            return

        filesize = int(parts[1])
        sock.sendall(b"READY")

        filepath = os.path.join(CLIENT_FILES_DIR, filename)
        received = 0
        with open(filepath, 'wb') as f:
            while received < filesize:
                chunk = sock.recv(min(BUFFER_SIZE, filesize - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)

        print(f"[INFO] File '{filename}' ({filesize} bytes) berhasil diunduh ke '{CLIENT_FILES_DIR}/'")
    finally:
        is_transferring.clear()


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        print(f"[INFO] Terhubung ke server {HOST}:{PORT}")
        print("[INFO] Perintah: /list | /upload <file> | /download <file> | ketik pesan untuk broadcast")
    except ConnectionRefusedError:
        print(f"[ERROR] Tidak bisa terhubung ke {HOST}:{PORT}.")
        return

    t = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    t.start()

    while True:
        try:
            user_input = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Keluar.")
            sock.close()
            break

        if not user_input:
            continue

        if user_input == '/list':
            sock.sendall(b"LIST|")
        elif user_input.startswith('/upload '):
            filename = user_input[8:].strip()
            if filename:
                send_file(sock, filename)
        elif user_input.startswith('/download '):
            filename = user_input[10:].strip()
            if filename:
                download_file(sock, filename)
        else:
            sock.sendall(f"MSG|{user_input}".encode())


if __name__ == '__main__':
    main()