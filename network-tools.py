import pickle
import socket


def msg_send(sock, msg):
    # 向客户端发送数据
    data_bytes = pickle.dumps(msg)
    data_size = len(data_bytes)
    print('数据大小：', data_size)
    header_bytes = data_size.to_bytes(4, byteorder='big')

    sock.sendall(header_bytes)
    print('数据header已发送')
    sock.sendall(data_bytes)
    print('数据body已发送')


def msg_recv(sock):
    header_bytes = sock.recv(4)
    data_size = int.from_bytes(header_bytes, byteorder='big')
    data_bytes = bytearray()
    while len(data_bytes) < data_size:
        print("接收数据中...")
        chunk = sock.recv(1024)
        data_bytes.extend(chunk)
    print('数据接收结束')

    msg = pickle.loads(data_bytes)
    return msg
