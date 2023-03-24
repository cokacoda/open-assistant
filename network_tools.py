import core
import pickle
import socket


def msg_send(sock, msg, dev=False):
    # 向客户端发送数据
    data_bytes = pickle.dumps(msg)
    data_size = len(data_bytes)
    core.dev_print(dev, 'Data length：', data_size)
    header_bytes = data_size.to_bytes(4, byteorder='big')

    sock.sendall(header_bytes)
    core.dev_print(dev, 'Data header has been sent')
    sock.sendall(data_bytes)
    core.dev_print(dev, 'Data body has been sent')


def msg_recv(sock, dev=False):
    header_bytes = sock.recv(4)
    data_size = int.from_bytes(header_bytes, byteorder='big')
    data_bytes = bytearray()
    while len(data_bytes) < data_size:
        core.dev_print(dev, 'Receiving data...')
        chunk = sock.recv(1024)
        data_bytes.extend(chunk)
    core.dev_print(dev, 'Data received')

    msg = pickle.loads(data_bytes)
    return msg
