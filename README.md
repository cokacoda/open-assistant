# Introduction

open-assistant is a program that automatically translates a document, including LaTeX documents, to another language and saves the result as a file. It can also be used for basic conversations.

# Stand-alone Mode

You can directly use this machine to communicate with the openai server.

**Example**:

```python
import openai
import core

openai.api_key_path = "/api_path/api.txt"

implictTex = core.Communication(default_language="Chinese")
res = implictTex.translate_file(filepath="/tex_path/file.tex",
                                original_language="English", target_language="Chinese", latex=True)
core.Communication.write_to_file(res, "/output_path/output_test.tex")
```

# Client-Server Mode

You can also deploy a server to forward the communication between you (the client) and the openai server.

**Example**:

Server side:

```bash
python3 assistant_server.py <server-ip> <server-port>
```

Client side:

```python
import sys

sys.path.append('/mnt/d/OneDrive/MyPrograms/open-assistant')
import assistant_client

server_ip_address = "server-ip"
server_listen_port = 12345 # write your <server-port>, 12345 is an example
myapi = "your api of openai"

test = assistant_client.ComClient(server_ip_address=server_ip_address, server_port=server_listen_port, api=myapi)

test.continue_conversation("hello")
print(test.get_last_response_content())
#%%

```