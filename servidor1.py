import socket
from utils import *


HOST = '0.0.0.0'  
PORT = 65431

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"Servidor 1 ouvindo em {HOST}:{PORT}")

    conn, addr = server.accept()
    print(f"Conectado a {addr}")

    # Receber dados
    size_bytes = conn.recv(4)
    size = int.from_bytes(size_bytes, 'big')
    data = conn.recv(size)
    A_block, B = deserialize_data(data)

    print("Recebido bloco de A:\n", A_block)
    print("Recebida matriz B:\n", B)

    # Calcular
    result = multiply_block(A_block, B)

    # Enviar resultado
    res_data = serialize_data(result)
    size = len(res_data)
    conn.sendall(size.to_bytes(4, 'big'))
    conn.sendall(res_data)

    print("Resultado enviado.")
    conn.close()
    server.close()

if __name__ == "__main__":
    main()