import socket
import threading
import numpy as np
from utils import serialize_data, deserialize_data

def input_matrix(name):
    print(f"Insira a matriz {name} (linha por linha, separada por espaços):")
    rows = int(input(f"Quantas linhas tem a matriz {name}? "))
    cols = int(input(f"Quantas colunas tem a matriz {name}? "))
    matrix = []
    for i in range(rows):
        while True:
            try:
                row = list(map(float, input(f"Linha {i+1}: ").split()))
                if len(row) != cols:
                    print(f"Erro: precisa ter {cols} colunas.")
                    continue
                matrix.append(row)
                break
            except ValueError:
                print("Entrada inválida. Use números separados por espaço.")
    return np.array(matrix)

HOST = '0.0.0.0'  # Aceita conexões de qualquer IP
PORT = 65432

def recv_all(conn, size):
    data = b""
    while len(data) < size:
        packet = conn.recv(size - len(data))
        if not packet:
            raise ConnectionError("Conexão encerrada pelo cliente.")
        data += packet
    return data

def handle_client(conn, idx, results, A_blocks, B):
    data = serialize_data((A_blocks[idx], B))
    size = len(data)
    conn.sendall(size.to_bytes(4, 'big'))
    conn.sendall(data)

    size_data = conn.recv(4)
    if not size_data:
        conn.close()
        return
    size = int.from_bytes(size_data, 'big')
    response = recv_all(conn, size)
    result_block = deserialize_data(response)
    results[idx] = result_block

    conn.close()

def main():
    A = input_matrix("A")
    print("Matriz A:\n", A)

    num_clients = 1  # Vamos usar 1 cliente
    rows_per_block = len(A) // num_clients
    A_blocks = [A[i:i + rows_per_block] for i in range(0, len(A), rows_per_block)]

    if len(A_blocks) > num_clients:
        A_blocks[-2] = np.vstack([A_blocks[-2], A_blocks[-1]])
        A_blocks = A_blocks[:-1]

    results = [None] * len(A_blocks)

    print("Aguardando conexão do cliente...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(num_clients)

    # Recebe a matriz B do cliente
    conn, addr = server.accept()
    print(f"Cliente {addr} conectado.")

    size_data = conn.recv(4)
    size = int.from_bytes(size_data, 'big')
    data = conn.recv(size)
    B = deserialize_data(data)
    print("Matriz B recebida do cliente:\n", B)

    # Verifica compatibilidade
    if A.shape[1] != B.shape[0]:
        print("Erro: A e B não são compatíveis para multiplicação.")
        conn.close()
        server.close()
        return

    # Envia blocos para processamento
    t = threading.Thread(target=handle_client, args=(conn, 0, results, A_blocks, B))
    t.start()
    t.join()

    server.close()

    C = np.vstack(results)
    print("Matriz resultante C = A * B:\n", C)

if __name__ == "__main__":
    main()