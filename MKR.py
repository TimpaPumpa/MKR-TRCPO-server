import socket
import struct
import pickle
import concurrent.futures
import numpy as np  

HOST = '0.0.0.0'
PORT = 65434

def recv_all(sock, length):
    """Функція, що зчитує задану кількість байтів."""
    data = b''
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            return None
        data += packet
    return data

def handle_client(conn, addr):
    print(f"[{addr}] Почав обробку клієнта")
    try:
        # 1. Зчитаємо розміри N, M, L (по 4 байти на кожне int32)
        header = recv_all(conn, 12)  # 3 int32 -> 3*4 = 12 байт
        if not header:
            return
        N, M, L = struct.unpack('!iii', header)  # big-endian, наприклад

        # 2. Зчитаємо обидві матриці
        #    Можна, наприклад, передавати у форматі pickle або будь-якому іншому
        #    Для прикладу - pickle (але для великих даних це може бути громіздко)
        #    Спочатку зчитаємо int32 - довжину байтового потоку для першої матриці
        length_1_bytes = recv_all(conn, 4)
        length_1 = struct.unpack('!i', length_1_bytes)[0]
        pickled_matrix_1 = recv_all(conn, length_1)

        #    Розпаковуємо матрицю 1
        mat1 = pickle.loads(pickled_matrix_1)

        #    Аналогічно для матриці 2
        length_2_bytes = recv_all(conn, 4)
        length_2 = struct.unpack('!i', length_2_bytes)[0]
        pickled_matrix_2 = recv_all(conn, length_2)

        mat2 = pickle.loads(pickled_matrix_2)

        # 3. Перемноження матриць (у паралельному режимі)
        #    Якщо використовуємо numpy, то воно і так на C оптимізоване.
        result = np.dot(mat1, mat2)

        # 4. Відправляємо результат назад клієнту
        #    Знову ж, можна pickle
        pickled_result = pickle.dumps(result)
        #    Спочатку довжину:
        conn.sendall(struct.pack('!i', len(pickled_result)))
        #    Потім самі дані:
        conn.sendall(pickled_result)

    except Exception as e:
        print(f"[{addr}] Помилка: {e}")
    finally:
        conn.close()
        print(f"[{addr}] З'єднання закрито")


def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Сервер слухає на порту {PORT}...")

        # Створюємо пул потоків, наприклад на 5 або 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            while True:
                conn, addr = s.accept()
                # Передаємо роботу в пул
                executor.submit(handle_client, conn, addr)

if __name__ == "__main__":
    run_server()
