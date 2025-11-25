import socket
import numpy as np
import time
import matplotlib.pyplot as plt  # ← Importação necessária para o gráfico

from utils import serialize_data, deserialize_data

def input_matrix(name):
    print(f"Configurando a matriz {name}:")
    rows = int(input(f"Quantas linhas tem a matriz {name}? "))
    cols = int(input(f"Quantas colunas tem a matriz {name}? "))
    print(f"Gerando matriz {name} aleatória de tamanho {rows}x{cols}...")
    # Gera matriz com valores inteiros entre 0 e 9 (você pode mudar o intervalo)
    matrix = np.random.randint(-100, 100, size=(rows, cols)).astype(float)
    return matrix

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
    
    ip1 = input("Digite o ip do servidor 1 (ex: 192.168.1.105)\n")
    ip2 = input("Digite o ip do servidor 2 (ex: 192.168.1.105)\n")
    
    print("\n[Modo DISTRIBUÍDO] Iniciando cálculo distribuído...")

    # Dividir A em 2 blocos
    half = len(A) // 2
    if half == 0:
        half = 1
    A1 = A[:half]
    A2 = A[half:]

    # Conectar a servidores
    conn1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        conn1.connect((ip1, 65431))
        conn2.connect((ip2, 65432))

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

        # Verificar igualdade
        if not np.allclose(C_serial, C_dist):
            print("❌ Resultados diferentes!")
            return

        # -------------------------------------------------
        # Plotar Gráfico
        # -------------------------------------------------
        labels = ['Serial', 'Distribuído']
        times = [time_serial, time_dist]
        speedup = time_serial / time_dist if time_dist > 0 else float('inf')

        fig, ax1 = plt.subplots(figsize=(8, 5))
        bars = ax1.bar(labels, times, color=['steelblue', 'tomato'])
        ax1.set_ylabel('Tempo (segundos)', color='black')
        ax1.set_title(f'Multiplicação de Matrizes: Serial vs Distribuído\nAceleração = {speedup:.2f}x')
        ax1.tick_params(axis='y', labelcolor='black')

        # Adicionar valores nas barras
        for bar, t in zip(bars, times):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(times)*0.01,
                     f'{t:.4f}s', ha='center', va='bottom')

        plt.tight_layout()
        plt.show()

        print("\n" + "="*50)
        print("RESULTADOS:")
        print("="*50)
        print(f"Tempo SERIAL:     {time_serial:.4f} s")
        print(f"Tempo DISTRIBUÍDO: {time_dist:.4f} s")
        print(f"Aceleração:       {speedup:.2f}x")
        print("✅ Resultados idênticos!")
        print("\nMatriz Resultante C = A × B:\n", C_serial)

    except Exception as e:
        print(f"Erro durante a execução distribuída: {e}")
    finally:
        conn1.close()
        conn2.close()

if __name__ == "__main__":
    main()