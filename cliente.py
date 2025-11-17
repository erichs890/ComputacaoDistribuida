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

    HOST = input("Digite o IP do servidor: ").strip()
    PORT = 65432

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    # Envia B para o servidor
    data = serialize_data(B)
    size = len(data)
    client.sendall(size.to_bytes(4, 'big'))
    client.sendall(data)

    # Recebe bloco A e faz multiplicação
    size_data = client.recv(4)
    size = int.from_bytes(size_data, 'big')
    data = client.recv(size)
    A_block, B = deserialize_data(data)

    print(f"Cliente recebeu bloco A:\n{A_block}")

    result = multiply_block(A_block, B)

    # Envia resultado
    response = serialize_data(result)
    size = len(response)
    client.sendall(size.to_bytes(4, 'big'))
    client.sendall(response)

    client.close()

if __name__ == "__main__":
    main()