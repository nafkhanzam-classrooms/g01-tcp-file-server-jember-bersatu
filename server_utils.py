import os

SERVER_FILES_DIR = "server_files"
BUFFER_SIZE = 4096

os.makedirs(SERVER_FILES_DIR, exist_ok=True)


def handle_list():
    """Kembalikan daftar file di folder server sebagai bytes."""
    files = os.listdir(SERVER_FILES_DIR)
    if files:
        return ("FILES:\n" + "\n".join(files)).encode()
    else:
        return b"FILES:\n(folder kosong)"


def receive_file(conn, filename, filesize):
    """
    Terima file dari client (binary-safe).
    conn   : socket client
    filename: nama file yang akan disimpan
    filesize: ukuran file dalam bytes
    """
    conn.sendall(b"READY")

    filepath = os.path.join(SERVER_FILES_DIR, filename)
    received = 0
    with open(filepath, "wb") as f:
        while received < filesize:
            chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)
    return received


def send_file(conn, filename):
    """
    Kirim file ke client (binary-safe).
    Kembalikan True jika berhasil, False jika file tidak ditemukan.
    """
    filepath = os.path.join(SERVER_FILES_DIR, filename)
    if not os.path.isfile(filepath):
        conn.sendall(f"ERROR|File '{filename}' tidak ditemukan di server.".encode())
        return False

    filesize = os.path.getsize(filepath)
    conn.sendall(f"OK|{filesize}".encode())

    # Tunggu ACK dari client
    ack = conn.recv(BUFFER_SIZE)
    if ack != b"READY":
        return False

    sent = 0
    with open(filepath, "rb") as f:
        while sent < filesize:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            conn.sendall(chunk)
            sent += len(chunk)
    return True


def parse_message(data: bytes):
    """
    Parse pesan dari client.
    Format yang dikenal:
      LIST|
      UPLOAD|filename|filesize
      DOWNLOAD|filename
      MSG|teks pesan broadcast
    Kembalikan tuple (command, args_dict)
    """
    text = data.decode(errors="replace")
    parts = text.split("|", 2)
    cmd = parts[0].upper()

    if cmd == "LIST":
        return ("LIST", {})
    elif cmd == "UPLOAD" and len(parts) >= 3:
        return ("UPLOAD", {"filename": parts[1], "filesize": int(parts[2])})
    elif cmd == "DOWNLOAD" and len(parts) >= 2:
        return ("DOWNLOAD", {"filename": parts[1]})
    elif cmd == "MSG" and len(parts) >= 2:
        return ("MSG", {"text": parts[1]})
    else:
        return ("UNKNOWN", {"raw": text})


def broadcast(clients, sender_addr, message: str):
    """
    Kirim pesan ke semua client kecuali pengirim.
    clients: dict {conn: addr} atau list conn
    """
    msg_bytes = f"[Broadcast dari {sender_addr}]: {message}".encode()
    if isinstance(clients, dict):
        for conn, addr in list(clients.items()):
            if addr != sender_addr:
                try:
                    conn.sendall(msg_bytes)
                except Exception:
                    pass
    else:
        for conn in list(clients):
            try:
                conn.sendall(msg_bytes)
            except Exception:
                pass
