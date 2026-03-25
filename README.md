# [![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mRmkZGKe)
# Network Programming - Assignment G01

## Anggota Kelompok
| Name           | NRP        | Kelas     |
| ---            | ---        | ----------|
| Mahendra Agung Darmawan | 5025241032 | Progjar-C |
| Riyannizaar Dwi Amarullah | 5025241121 | Progjar-C |

Link Video Demo: [VIDEO DEMO](https://youtu.be/wOfvONG9eSU)

---

## Deskripsi Proyek
Proyek ini merupakan implementasi sistem komunikasi **Client-Server** berbasis protokol **TCP** yang mendukung fitur *real-time chat* dan transfer berkas *Upload/Download*. 

Berfokus pada perbandingan performa dan logika antara 4 arsitektur server berbeda (Sync, Threading, Select, dan Poll).

Sistem ini memungkinkan banyak klien untuk terhubung ke satu server pusat, saling bertukar pesan, dan mengelola berkas di folder server.

## Tujuan Utama:
1. Memahami Protokol TCP: Mengimplementasikan komunikasi data yang handal menggunakan **Socket Programming**.
2. Memahami **I/O Multiplexing** (Select & Poll).
3. Mengelola konkurensi dengan **Multithreading**.

---

## Struktur File
| File | Fungsi Utama | Deskripsi Teknis |
| :--- | :--- | :--- |
| `client.py` | **Client Terminal** | Interface user dengan background thread untuk menerima broadcast. |
| `server_utils.py` | **Helper Module** | Logic inti untuk pengiriman file dan pengelolaan directory. |
| `server_sync.py` | **Sync Server** | Model blocking, hanya melayani 1 user secara eksklusif. |
| `server_thread.py`| **Threaded Server** | *One-thread-per-connection* menggunakan `threading.Thread`. |
| `server_select.py`| **Select Server** | Multiplexing berbasis bitmap (cocok untuk lintas platform). |
| `server_poll.py`  | **Poll Server** | Multiplexing efisien berbasis event. |

---

## Penjelasan Program

Program ini dirancang dengan arsitektur **Modular**, di mana logika inti dipisahkan (membuat file `server_utils.py`) untuk memudahkan pemeliharaan kode dan perbandingan antar model server.

1.  **`client.py`**: Menggunakan pendekatan *Multithreading*. Satu thread utama menangani input dari pengguna (seperti perintah `/upload`, `/list`, dll), sementara satu thread *background* terus mendengarkan pesan *broadcast* dari server. Ini memastikan antarmuka klien tetap responsif meskipun server mengirimkan data secara tiba-tiba.
2.  **`server_utils.py`**: Berfungsi sebagai *engine* utama. Di sini terdapat protokol segmentasi data (chunking). Saat file dikirim, data dipecah menjadi bagian-bagian kecil (4096 bytes) untuk mencegah penggunaan memori yang berlebihan baik di sisi server maupun klien.
3.  **Mekanisme Server**:
    * **Sync**: Menggunakan socket standar yang bersifat *blocking*.
    * **Threading**: Memanfaatkan pustaka `threading` Python untuk membuat *sub-process* ringan setiap kali ada `accept()` koneksi baru.
    * **Select & Poll**: Menggunakan teknik **I/O Multiplexing**. Server memantau daftar *File Descriptor* (socket) yang aktif. Jika ada aktivitas (data masuk), sistem operasi akan memberi tahu server untuk memprosesnya. `Poll` lebih unggul di sistem Linux karena menggunakan struktur data yang lebih efisien (array) dibandingkan `Select` (bitmap).

---

## Fitur & Protokol
Sistem menggunakan prefix perintah untuk membedakan jenis data:
* `LIST|`: Meminta daftar file di folder `server_files`.
* `UPLOAD|<filename>`: Protokol pengiriman file dari klien ke server.
* `DOWNLOAD|<filename>`: Protokol pengambilan file dari server ke klien.
* `MSG|<content>`: Pesan chat biasa yang akan di-*broadcast*.

---

## Screenshot Hasil & Pembahasan

### 1. Hasil Pengujian Synchronous
![alt text](image.png)
**Analisis:** Pada screenshot ini terlihat bahwa saat Klien A terhubung, Klien B yang mencoba masuk tidak mendapatkan respon apa pun dari server. Hal ini terjadi karena thread utama server "terkunci" pada fungsi `recv()` milik Klien A. Koneksi Klien B baru diproses setelah *socket* Klien A ditutup.

### 2. Hasil Pengujian Threading
![alt text](image-1.png) 
**Analisis:** Screenshot menunjukkan Klien A sedang melakukan proses `/upload` file, namun di saat yang sama, pesan chat dari Klien B tetap muncul di layar. Ini membuktikan bahwa setiap klien memiliki *resource* CPU masing-masing dalam bentuk thread, sehingga operasi I/O yang berat tidak menghentikan layanan untuk klien lain.

### 3. Hasil Pengujian Select & Poll
![alt text](image-2.png)
![alt text](image-3.png)
**Analisis:** Terlihat di terminal server bahwa sistem mampu mengelola lebih dari dua klien secara bersamaan dalam satu iterasi *loop*. Perbedaan utama pada screenshot `Poll` (di WSL) adalah kemampuannya menangani banyak koneksi tanpa batasan jumlah socket, berbeda dengan `Select` yang memiliki limitasi.

---

## Cara Menjalankan

### 1. Persiapan Folder
Pastikan struktur folder Anda seperti ini:
```
.
├── client.py           # Client universal, dipakai untuk semua server
├── server_utils.py     # Modul utilitas bersama protokol, file I/O
├── server-sync.py      # Server Synchronous
├── server-select.py    # Server dengan select.select()
├── server-poll.py      # Server dengan select.poll() (Linux/macOS only)
├── server-thread.py    # Server dengan threading
├── server_files/       # Folder file di sisi server (otomatis dibuat)
└── client_files/       # Folder file di sisi client (otomatis dibuat)
```

### 2. Persiapan Umum (Bahan Uji)
Buat satu file teks di client_files/testing.txt (isinya bebas) sebagai bahan upload.

### 3. Pengujian 1: Server Synchronous (`server_sync.py`)
1. Terminal 1: Jalankan python server_sync.py.
2. Terminal 2 (Klien A): Jalankan python client.py. Ketik pesan: Halo, saya Klien A.
3. Terminal 3 (Klien B): Jalankan python client.py. Ketik pesan: Halo, saya Klien B.
4. Observasi: Lihat di Terminal 3, apakah pesan Klien B muncul? (seharusnya tidak muncul di server sampai Klien A keluar).
5. Terminal 2: Exit (CTRL-C).
6. Observasi Akhir: Begitu Klien A keluar, tiba-tiba pesan Klien B yang tadi tertahan akan langsung muncul di server.
    Kesimpulan Laporan: Server Sync hanya bisa menangani 1 klien secara eksklusif.

### 4. Pengujian 2: Server Threading (`server_thread.py`)
1. Terminal 1: Jalankan python server_thread.py.
2. Terminal 2 (Klien A): Jalankan python client.py.
3. Terminal 3 (Klien B): Jalankan python client.py.
4. Lakukan hal berikut:
- Di Klien A: Ketik /upload testing.txt.
- Tepat saat upload berjalan, di Klien B: Ketik pesan apa saja saat upload.
5. Observasi:
- Pesan Klien B harus langsung muncul di server dan di layar Klien A tanpa menunggu upload selesai.
- Kesimpulan Laporan: Threading memungkinkan skalabilitas paralel, setiap klien punya jalur (thread) sendiri.

### 5. Pengujian 3: Server Select (`server_select.py`)
1. Terminal 1: Jalankan python server_select.py.
2. Terminal 2 (Klien A): Jalankan python client.py.
3. Terminal 3 (Klien B): Jalankan python client.py.
4. Lakukan hal berikut:
- Lakukan chat bolak-balik antara Klien A dan Klien B.
- Cek daftar file dengan /list.
5. Observasi:
- Semua fitur berjalan lancar seperti model Threading, tapi bedanya di Terminal Server hanya ada satu proses utama yang bekerja (hemat RAM).
6. Tes Error: Hapus file testing.txt di client_files, lalu coba /download testing.txt.
- Kesimpulan Laporan: Select efisien untuk banyak koneksi ringan dalam satu loop tunggal.

### 6. Pengujian 4: Server Poll (`server_poll.py`)
1. Terminal 1 (Server): Jalankan python3 server_poll.py
2. Terminal 2 (Klien A): Jalankan python3 client.py
3. Terminal 3 (Klien B): Jalankan python3 client.py
4. Di Klien A (Terminal 2): Ketik /upload testing.txt
5. Sesaat setelah tekan Enter, di Klien B (Terminal 3): Ketik chat (bebas apa saja)
6. Di Klien B (Terminal 3): Ketik /list
7. Hapus file di client_files lewat Terminal WSL: rm client_files/testing.txt.
6. Coba download kembali di Klien B: >> /download testing.txt.
7. Pastikan file muncul kembali secara utuh.

## Perbandingan 4 Jenis Server
 
| Aspek              | sync                     | select                          | poll                             | thread                          |
|-------------------|--------------------------|----------------------------------|----------------------------------|----------------------------------|
| Multi-client       | ❌ (1 saja)              | ✅                               | ✅                               | ✅                               |
| Threading          | ❌                       | ❌                               | ❌                               | ✅                               |
| Platform           | Semua                    | Semua                            | Linux/macOS                      | Semua                            |
| Batas koneksi      | 1                        | ~64 (Windows)                    | Tidak ada (lebih scalable)       | Tergantung RAM                   |
| Kelebihan          | Sederhana, mudah dipahami| Tidak perlu thread, ringan       | Lebih efisien dari select        | Mudah implementasi multi-client  |
|                   | Debugging mudah          | Cocok untuk jumlah client kecil  | Cocok untuk banyak koneksi       | Responsif (paralel)              |
| Kekurangan         | Tidak scalable           | Ada limit socket (terutama Win)  | Lebih kompleks dari select       | Overhead thread tinggi           |
|                   | Blocking (client lain nunggu)| Kurang efisien untuk banyak client | Tidak tersedia di Windows penuh | Bisa boros memori & CPU          |


