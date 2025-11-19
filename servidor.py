import socket
import threading
import numpy as np
import time
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
            raise ConnectionError("Conexão encerrada.")
        data += packet
    return data

def main():
    # 1. Receber A no servidor
    A = input_matrix("A")
    print("Matriz A:\n", A)

    print("Aguardando conexão do cliente para receber matriz B...")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)

    conn, addr = server.accept()
    print(f"Cliente {addr} conectado.")

    # 2. Receber B do cliente
    size_bytes = conn.recv(4)
    if not size_bytes:
        print("Erro: cliente não enviou matriz B.")
        return
    size = int.from_bytes(size_bytes, 'big')
    data = recv_all(conn, size)
    B = deserialize_data(data)
    print("Matriz B recebida:\n", B)

    if A.shape[1] != B.shape[0]:
        print("Erro: matrizes incompatíveis!")
        conn.close()
        server.close()
        return

    # -------------------------------------------------
    # 3. Cálculo SERIAL (tudo local, para comparação)
    # -------------------------------------------------
    print("\n[Modo SERIAL] Calculando localmente...")
    start_serial = time.time()
    C_serial = np.dot(A, B)
    end_serial = time.time()
    time_serial = end_serial - start_serial
    print(f"✅ Serial concluído em {time_serial:.4f} segundos.")

    # -------------------------------------------------
    # 4. Cálculo DISTRIBUÍDO
    # -------------------------------------------------
    print("\n[Modo DISTRIBUÍDO] Iniciando cálculo distribuído...")

    # Dividir A em 2 partes
    half = len(A) // 2
    if half == 0:
        half = 1
    A_server = A[:half]
    A_client = A[half:]

    results = [None, None]

    # Servidor calcula sua parte
    start_dist = time.time()
    results[0] = multiply_block(A_server, B)

    # Enviar bloco para cliente
    payload = serialize_data((A_client, B))
    size = len(payload)
    conn.sendall(size.to_bytes(4, 'big'))
    conn.sendall(payload)

    # Esperar resultado do cliente
    def handle_client_result():
        try:
            size_bytes = recv_all(conn, 4)
            size = int.from_bytes(size_bytes, 'big')
            res_data = recv_all(conn, size)
            results[1] = deserialize_data(res_data)
        except Exception as e:
            print(f"[Erro] Cliente falhou: {e}")

    client_thread = threading.Thread(target=handle_client_result)
    client_thread.start()
    client_thread.join(timeout=10)

    # Finalizar tempo
    end_dist = time.time()
    time_dist = end_dist - start_dist

    if results[1] is None:
        print("Erro: cliente não retornou resultado.")
        return

    C_dist = np.vstack([results[0], results[1]])

    # -------------------------------------------------
    # 5. Comparação
    # -------------------------------------------------
    print("\n" + "="*50)
    print("RESULTADOS:")
    print("="*50)
    print(f"Tempo SERIAL:     {time_serial} segundos")
    print(f"Tempo DISTRIBUÍDO: {time_dist} segundos")
    print(f"Aceleração:       {time_serial / time_dist}x" if time_dist > 0 else "Infinito")

    # Verificar se os resultados são iguais (dentro de uma tolerância)
    if np.allclose(C_serial, C_dist):
        print("✅ Resultados idênticos!")
    else:
        print("❌ Resultados diferentes!")

    print("\nMatriz Resultante C = A × B:\n", C_serial)

    server.close()

if __name__ == "__main__":
    main()