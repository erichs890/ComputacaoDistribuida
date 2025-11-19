import socket
import threading
import numpy as np
from utils import serialize_data, deserialize_data, multiply_block

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

HOST = '0.0.0.0'
PORT = 65432

def recv_all(conn, size):
    data = b""
    while len(data) < size:
        packet = conn.recv(size - len(data))
        if not packet:
            raise ConnectionError("Conexão encerrada inesperadamente.")
        data += packet
    return data

def handle_client(conn, results, idx):
    try:
        # Receber tamanho do resultado
        size_bytes = recv_all(conn, 4)
        size = int.from_bytes(size_bytes, 'big')
        # Receber resultado
        res_data = recv_all(conn, size)
        results[idx] = deserialize_data(res_data)
        print(f"[Servidor] Resultado do cliente {idx} recebido com sucesso.")
    except Exception as e:
        print(f"[Erro no cliente {idx}]: {e}")
        results[idx] = None
    finally:
        conn.close()

def main():
    A = input_matrix("A")
    print("Matriz A:\n", A)

    print("Aguardando conexão do cliente para receber matriz B...")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)

    conn, addr = server.accept()
    print(f"Cliente {addr} conectado.")

    try:
        # Receber B do cliente
        size_bytes = conn.recv(4)
        if not size_bytes:
            raise ConnectionError("Falha ao receber tamanho de B.")
        size = int.from_bytes(size_bytes, 'big')
        data = recv_all(conn, size)
        B = deserialize_data(data)
        print("Matriz B recebida:\n", B)

        if A.shape[1] != B.shape[0]:
            print("Erro: matrizes incompatíveis para multiplicação!")
            conn.close()
            server.close()
            return

        # Dividir A em 2 blocos
        half = len(A) // 2
        if half == 0:
            half = 1  # Caso A tenha só 1 linha
        A_server = A[:half]
        A_client = A[half:]

        results = [None, None]

        # Servidor calcula sua parte
        results[0] = multiply_block(A_server, B)
        print("[Servidor] Parte local calculada.")

        # Enviar bloco para cliente
        payload = serialize_data((A_client, B))
        size = len(payload)
        conn.sendall(size.to_bytes(4, 'big'))
        conn.sendall(payload)

        # Receber resultado do cliente em thread
        client_thread = threading.Thread(target=handle_client, args=(conn, results, 1))
        client_thread.start()
        client_thread.join(timeout=10)  # Timeout de segurança

        if results[1] is None:
            print("Erro: cliente não retornou resultado.")
            return

        # Montar resultado final
        C = np.vstack([results[0], results[1]])
        print("\n✅ Resultado final C = A × B:\n", C)

    except Exception as e:
        print(f"Erro no servidor: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    main()