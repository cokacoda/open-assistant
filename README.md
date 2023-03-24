# open-assistant
A program that automatically translates a document, including LaTeX documents, to another language and saves the result as a file. It can also be used for basic conversations.

Example:

```python
import openai
import core

openai.api_key_path = "/api_path/api.txt"

implictTex = core.Communication(default_language="Chinese")
res = implictTex.translate_file(filepath="/tex_path/file.tex",
                                original_language="English", target_language="Chinese", latex=True)
core.Communication.write_to_file(res, "/output_path/output_test.tex")
```
