import socket
from utils import serialize_data, deserialize_data, multiply_block

HOST = '0.0.0.0'
PORT = 65431  # servidor1

def receve_all(conn, size): 
    data = b""
    while len(data) < size:
        packet = conn.recv(size - len(data))
        if not packet:
            raise ConnectionError("Conexão encerrada.")
        data += packet
    return data

def main():
    print(f"Servidor 1 iniciado. Aguardando conexão em {HOST}:{PORT}...")


    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)

    conn, addr = server.accept()

    print(f"Cliente conectado: {addr}")

    # Receber tamanho dos dados
    size_bytes = conn.recv(4)
    if not size_bytes:
        print("Erro: não recebeu tamanho dos dados.")
        conn.close()
        server.close()
        return

    size = int.from_bytes(size_bytes, 'big')
    print(f"Recebendo {size} bytes de dados...")

    # Receber dados completos
    data = receve_all(conn, size)
    A_block, B = deserialize_data(data)

    print("\nDADOS RECEBIDOS:")
    print("Bloco de A atribuído a este servidor:")
    print(A_block)
    print("\nMatriz B inteira (para multiplicação):")
    print(B)

    print("\nCALCULANDO: C_block = A_block × B...")
    result = multiply_block(A_block, B)
    print("Cálculo concluído. Resultado parcial:")
    print(result)

    # Enviar resultado
    res_data = serialize_data(result)
    res_size = len(res_data)
    conn.sendall(res_size.to_bytes(4, 'big'))
    conn.sendall(res_data)

    print(f"\nEnviado {res_size} bytes de resultado ao cliente.")
    print("Conexão encerrada.\n")

    conn.close()
    server.close()

main()
