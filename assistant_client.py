import openai
import socket
import time
import core
import network_tools


class ComClient(core.Communication):
    def __init__(self, server_ip_address, server_port, api,
                 model="gpt-3.5-turbo", default_language="English", dev=False):
        super().__init__(model=model, default_language=default_language, dev=dev)
        self.server_ip_address = server_ip_address
        self.server_port = server_port
        self.api = api

    def send_messages(self, next_user_message, additional_args):
        meta = {"api": self.api}
        kwargs = {
            "model": self.model,
            "messages": self.messages[self.messages_start_index:] + [next_user_message],
            "stop": None
        }
        kwargs = kwargs | additional_args
        request = [meta, kwargs]

        socket_connection_error_number = 0

        while True:
            try:
                # 创建 socket 对象
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # 设置超时时间为 10 秒
                client_socket.settimeout(5 * 60)

                # 连接服务器
                core.dev_print(self.dev, 'Connecting server at ', self.server_ip_address)
                server_address = (self.server_ip_address, self.server_port)
                client_socket.connect(server_address)
                core.dev_print(self.dev, 'Connection established')

                # 向服务器发送数据
                network_tools.msg_send(client_socket, request)

                # 接收服务器数据
                response = network_tools.msg_recv(client_socket)
                core.dev_print(self.dev, 'Data received :\n', response)
                state_code = response[0]

                # 关闭 socket 连接
                client_socket.close()
                core.dev_print(self.dev, 'Connection closed')

                if state_code != 0:
                    if state_code == 1:
                        raise core.Communication.MaxInputTokenExceededError("Max input token limit exceeded")
                    elif state_code == 1.1:
                        raise openai.error.InvalidRequestError(response[1].message, response[1].param)  # dev:!需要确认
                    elif state_code == 2:
                        print("Connection error. Retrying in 10 seconds.")
                        time.sleep(10)
                    else:
                        raise core.Communication.UnKnownOpenAIError(response)
                else:
                    return response[1]

            except socket.timeout:
                print('Connection time out')
                socket_connection_error_number = socket_connection_error_number + 1
                if socket_connection_error_number >= 5:
                    raise socket.timeout

            except socket.error as e:
                print('Connection error：', e)
                socket_connection_error_number = socket_connection_error_number + 1
                if socket_connection_error_number >= 5:
                    raise socket.error
