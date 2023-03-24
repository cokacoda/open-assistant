import socket
import openai
import os
import network_tools
import core
import sys


class ComServer:
    def __init__(self, address, port, dev=False):
        self.address = address
        self.port = port
        self.dev = dev

    def start(self):
        # 创建 TCP/IP 套接字
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 绑定到本地端口
        server_address = (self.address, self.port)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(server_address)

        # 开始监听传入的连接
        max_connections = 10
        server_socket.listen(max_connections)

        while True:
            core.dev_print(self.dev, "Waiting for client's connection")
            client_socket, client_address = server_socket.accept()
            core.dev_print(self.dev, "Client connected: ", client_address)

            # 接收客户端数据
            request = network_tools.msg_recv(client_socket)
            core.dev_print(self.dev, "Client request received:\n", request)

            # 向客户端发送数据
            response = forward_request(client_address[0], client_address[1], request)
            core.dev_print(self.dev, "Forward request finished")
            network_tools.msg_send(client_socket, response)
            core.dev_print(self.dev, "Response resent to client")

            # 关闭客户端连接
            client_socket.close()
            core.dev_print(self.dev, "Client connection closed")


def forward_request(ip, port, args):
    user_api = args[0]["api"]
    api_path = "" + ip + "-" + str(port) + ".api.txt"
    with open(api_path, "w") as f:
        f.write(user_api)

    kwargs = args[1]
    success = False
    openai.api_key_path = api_path
    try:
        msg = openai.ChatCompletion.create(**kwargs)
        success = True

    except openai.error.InvalidRequestError as e:
        # If the message exceeds the max token limit, raise a MaxInputTokenExceededError.
        # 如果消息超过了最大标记限制，则引发MaxInputTokenExceededError异常
        if "Please reduce the length of the messages." in str(e):
            msg = [1, str(e)]
        else:
            msg = [1.1, str(e)]
    except openai.error.APIConnectionError as e:
        msg = [2, str(e)]

    finally:
        if success:
            response = [0, msg]
        else:
            response = msg

        os.remove(api_path)
        return response


def start_server(address, port, dev=False):
    cs = ComServer(address=address, port=port, dev=dev)
    cs.start()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 " + sys.argv[0] + " <server ip address> <port> (<bool of develop mode> default False)")
        exit(1)

    if len(sys.argv) == 4:
        dev = (sys.argv[3] == "True")
    else:
        dev = False
    start_server(sys.argv[1], int(sys.argv[2]), dev=dev)
