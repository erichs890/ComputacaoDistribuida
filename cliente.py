import socket
import numpy as np
import time
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

def recv_all(conn, size):
    data = b""
    while len(data) < size:
        packet = conn.recv(size - len(data))
        if not packet:
            raise ConnectionError("Conexão encerrada.")
        data += packet
    return data

def main():
    A = input_matrix("A")
    B = input_matrix("B")
    print("\nMatriz A:\n", A)
    print("Matriz B:\n", B)

    if A.shape[1] != B.shape[0]:
        print("Erro: matrizes incompatíveis!")
        return

    # -------------------------------------------------
    # Cálculo SERIAL
    # -------------------------------------------------
    print("\n[Modo SERIAL] Calculando localmente...")
    start_serial = time.time()
    C_serial = np.dot(A, B)
    end_serial = time.time()
    time_serial = end_serial - start_serial
    print(f"✅ Serial concluído em {time_serial:.4f} segundos.")

    # -------------------------------------------------
    # Cálculo DISTRIBUÍDO
    # -------------------------------------------------
    print("\n[Modo DISTRIBUÍDO] Iniciando cálculo distribuído...")

    # Dividir A em 2 blocos
    half = len(A) // 2
    if half == 0:
        half = 1
    A1 = A[:half]
    A2 = A[half:]

    # Conectar a servidores
    conn1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn1.connect(('0.0.0.0', 65431)) #Por ip do servidor 1

    conn2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn2.connect(('0.0.0.0', 65432)) #Por ip do servidor 2

    # Enviar blocos para cada servidor
    start_dist = time.time()

    # Enviar A1 e B para servidor1
    payload1 = serialize_data((A1, B))
    size1 = len(payload1)
    conn1.sendall(size1.to_bytes(4, 'big'))
    conn1.sendall(payload1)

    # Enviar A2 e B para servidor2
    payload2 = serialize_data((A2, B))
    size2 = len(payload2)
    conn2.sendall(size2.to_bytes(4, 'big'))
    conn2.sendall(payload2)

    # Receber resultados
    size_bytes1 = recv_all(conn1, 4)
    size1 = int.from_bytes(size_bytes1, 'big')
    res1 = recv_all(conn1, size1)
    result1 = deserialize_data(res1)

    size_bytes2 = recv_all(conn2, 4)
    size2 = int.from_bytes(size_bytes2, 'big')
    res2 = recv_all(conn2, size2)
    result2 = deserialize_data(res2)

    # Montar resultado final
    C_dist = np.vstack([result1, result2])
    end_dist = time.time()
    time_dist = end_dist - start_dist

    print(f"✅ Distribuído concluído em {time_dist:.4f} segundos.")

    # Comparar resultados
    print("\n" + "="*50)
    print("RESULTADOS:")
    print("="*50)
    print(f"Tempo SERIAL:     {time_serial:.4f} segundos")
    print(f"Tempo DISTRIBUÍDO: {time_dist:.4f} segundos")
    if time_dist > 0:
        print(f"Aceleração:       {time_serial / time_dist:.2f}x")
    else:
        print("Aceleração:       Infinito")

    if np.allclose(C_serial, C_dist):
        print("✅ Resultados idênticos!")
    else:
        print("❌ Resultados diferentes!")

    print("\nMatriz Resultante C = A × B:\n", C_serial)

    conn1.close()
    conn2.close()

if __name__ == "__main__":
    main()
