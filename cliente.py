import socket
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

def main():
    B = input_matrix("B")
    print("Matriz B:\n", B)

    HOST = input("IP do servidor: ").strip()
    PORT = 65432

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))

        # Enviar B
        data = serialize_data(B)
        size = len(data)
        client.sendall(size.to_bytes(4, 'big'))
        client.sendall(data)

        # Receber bloco de A + B
        size_bytes = client.recv(4)
        if not size_bytes:
            print("Erro: não recebeu tamanho do bloco.")
            return
        size = int.from_bytes(size_bytes, 'big')
        payload = client.recv(size)
        A_block, B = deserialize_data(payload)
        print("Bloco recebido para cálculo:\n", A_block)

        # Calcular localmente
        result = multiply_block(A_block, B)
        print("Resultado calculado:\n", result)

        # Enviar resultado
        res_data = serialize_data(result)
        size = len(res_data)
        client.sendall(size.to_bytes(4, 'big'))
        client.sendall(res_data)
        print("✅ Resultado enviado ao servidor.")

    except Exception as e:
        print(f"Erro no cliente: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()