import openai
import re
import time
import datetime


def dev_print(dev_bool, *dev_msg):
    if dev_bool:
        print(*dev_msg)


def split_text(text, separator="\n", max_length=2048):
    """
    Define a function that splits a given text into paragraphs of maximum length max_length with a given separator.
    If no separator is given, it will default to "\n".
    The function returns a list of strings, each string being a paragraph.

    定义一个函数，将给定文本按照指定的分隔符分成最大长度为max_length的段落，并使得分割的数量尽量小。
    如果没有给定分隔符，则默认使用 "\n"。
    该函数返回一个字符串列表，每个字符串代表一个段落。
    :param text:
    :param separator:
    :param max_length:
    :return:
    """

    # Split the text into lines using the separator
    # 使用分隔符将文本拆分成段
    lines = text.split(separator)

    # Initialize an empty list to hold the resulting paragraphs
    # 初始化一个空列表，用于存储结果段落
    result = []

    # Initialize an empty string to hold the current paragraph being built
    # 初始化一个空字符串，用于存储当前正在构建的段落
    current_paragraph = ""

    # Iterate over each line in the text
    # 遍历文本中的每一行
    for line in lines:

        # If adding the current line to the current paragraph would exceed the maximum length, append the current
        # paragraph to the result list and start a new current paragraph.
        # 如果将当前行添加到当前段落会导致长度超过最大值，将当前段落添加到结果列表中，并开始一个新的当前段落。
        if len(current_paragraph) + len(line) > max_length:
            result.append(current_paragraph)
            current_paragraph = ""

        # Add the current line to the current paragraph
        # 将当前行添加到当前段落中
        current_paragraph += line + separator

        # If the current paragraph is longer than the maximum length and ends with a word,
        # split the paragraph at the last word and append the first part to the result list.
        # 如果当前段落的长度超过最大值，并且以单词结尾，则将该段落从最后一个单词处分割，并将第一部分添加到结果列表中。
        if len(current_paragraph) >= max_length and re.search(r"\b\w+\b", current_paragraph[::-1]):
            match = re.search(r"\b\w+\b", current_paragraph[::-1])
            end = len(current_paragraph) - match.start()
            result.append(current_paragraph[:end])
            current_paragraph = current_paragraph[end:]

    # If there is a current paragraph that has not been added to the result list, add it to the result list.
    # 如果存在当前段落尚未添加到结果列表中，则将其添加到结果列表中。
    if current_paragraph:
        result.append(current_paragraph)

    # Return the result list of paragraphs
    # 返回段落结果列表
    return result


class Communication:
    """
    This Communication class is designed to enable users to communicate with OpenAI's pre-trained AI models using
    OpenAI's API. The class includes methods for sending messages and continuing conversations.

    这个Communication类旨在使用OpenAI的API使用户能够与OpenAI的预训练AI模型进行交互。该类包括发送消息和继续对话的方法。
    """

    def __init__(self, model="gpt-3.5-turbo", default_language="English"):
        # Initialize the Communication class with a given AI model and default language.
        # 初始化Communication类，包括默认AI模型、消息列表、历史记录列表、默认语言、消息开始索引等属性

        self.model = model
        self.messages = []
        self.history = []
        self.default_language = default_language
        self.messages_start_index = 0

    def continue_conversation(self, next_message, additional_args={}):
        """
        When a user sends a message to the AI model using the continue_conversation method, the method creates a
        next_user_message dictionary containing the user's message and a continue_message dictionary to prompt the
        user to continue the conversation. The method then sends the next_user_message to the AI model using the
        send_messages method and receives a response. If the response exceeds the maximum token limit, the method
        sends a continue_message to the AI model until the response no longer exceeds the maximum token limit.

        当用户使用continue_conversation方法向AI模型发送消息时，该方法创建一个包含用户消息的next_user_message字典
        和一个continue_message字典以提示用户继续对话。然后，该方法使用send_messages方法将next_user_message发送到AI模型并接收响应。
        如果响应超过最大标记限制，则该方法向AI模型发送一个continue_message，直到响应不再超过最大标记限制。

        :param next_message:
        :param additional_args:
        :return:
        """
        # Continues a conversation with the AI model by sending a user message and receiving a response.
        # 通过发送用户消息并接收响应，继续与AI模型进行对话。

        next_user_message = {"role": "user", "content": next_message}
        continue_message = {"role": "user", "content": self.continue_prompt_message()}
        responses = []

        while True:
            try:
                response = self.send_messages(next_user_message=next_user_message, additional_args=additional_args)
                self.write_result(next_user_message, response)
                responses.append(response)

                # If the response message exceeds the max token limit, continue the conversation.
                # 如果响应消息超过了最大标记限制，继续对话。
                while response['choices'][0]['finish_reason'] == "length":
                    next_user_message = continue_message
                    response = self.send_messages(next_user_message=next_user_message, additional_args=additional_args)
                    self.write_result(user_message=next_user_message, response=response)
                    responses.append(response)
                break

            except Communication.MaxInputTokenExceededError:
                # If the message exceeds the max token limit, adjust the messages_start_index
                # to reduce the amount of history being sent to the API.
                # 如果消息超过了最大标记限制，则调整messages_start_index以减少发送到API的历史记录量。

                if self.messages_start_index < len(self.messages):
                    self.messages_start_index = self.messages_start_index + 2
                else:
                    raise Communication.MaxInputTokenExceededError(
                        "Max input token limit exceeded and no more history is available. Please try to reduce max split length.")

        return responses

    def send_messages(self, next_user_message, additional_args):
        """
        The send_messages method sends messages to the AI model using OpenAI's API and returns the response. If the
        message exceeds the maximum token limit, the method raises a MaxInputTokenExceededError. The method also
        handles API connection errors and retries the API call after 10 seconds.

        send_messages方法使用OpenAI的API向AI模型发送消息并返回响应。如果消息超过了最大标记限制，
        该方法会引发MaxInputTokenExceededError。该方法还处理API连接错误，并在10秒后重试API调用。

        :param next_user_message:
        :param additional_args:
        :return:
        """
        # Sends messages to the AI model and returns the response.
        # 发送消息到AI模型并返回响应。

        kwargs = {
            "model": self.model,
            "messages": self.messages[self.messages_start_index:] + [next_user_message],
            "stop": None
        }
        kwargs = kwargs | additional_args

        while True:
            try:
                response = openai.ChatCompletion.create(**kwargs)
                break
            except openai.error.InvalidRequestError as e:
                # If the message exceeds the max token limit, raise a MaxInputTokenExceededError.
                # 如果消息超过了最大标记限制，则引发MaxInputTokenExceededError异常
                if "Please reduce the length of the messages." in str(e):
                    raise Communication.MaxInputTokenExceededError("Max input token limit exceeded")
                else:
                    raise e
            except openai.error.APIConnectionError as e:
                print("Connection error.\n", str(e), "\nRetrying in 10 seconds.")
                time.sleep(10)

        return response

    def continue_prompt_message(self):
        """
        The continue_prompt_message method returns a message to prompt the user to continue the conversation based on
        the default language specified in the Communication class.

        continue_prompt_message方法根据Communication类中指定的默认语言返回提示用户继续对话的消息。

        :return:
        """
        # Returns a message to prompt the user to continue the conversation.
        # 返回一个提示用户继续对话的消息。

        if self.default_language == "English":
            next_message = "Continue"
        elif self.default_language == "Chinese":
            next_message = "继续"
        else:
            next_message = "Continue"
        return next_message

    def write_result(self, user_message, response):
        """
        The write_result method writes the result of a conversation to the history and messages lists in the
        Communication class.

        这个 write_result 方法会把对话的结果写入 Communication 类中的 history 和 messages 列表中。

        :param user_message:
        :param response:
        :return:
        """
        # Writes the result of a conversation to the history and messages lists.

        self.history.append(response)
        role = response['choices'][0]['message']['role']
        content = response['choices'][0]['message']['content']
        self.messages.append(user_message)
        self.messages.append({"role": role, "content": content})

    def translate_file(self, filepath, original_language, target_language, latex, split_text_max_length=2500
                       , write_tmp=True):
        """
        The translate_file method reads the contents of a file and translates it from one language to another using
        OpenAI's API. If the contents of the file exceed a specified maximum length, the method splits the contents
        into smaller pieces. The translated content is returned in the form of a list of conversation history objects.

        translate_file方法从文件中读取内容，并使用OpenAI的API将其从一种语言翻译成另一种语言。如果文件内容超过了指定的最大长度，
        该方法将把内容分成更小的片段。翻译后的内容以对话历史对象的列表形式返回。

        :param write_tmp:
        :param filepath:
        :param original_language:
        :param target_language:
        :param latex:
        :param split_text_max_length:
        :return:
        """

        # Open the file and read its contents.
        # 打开文件并读取其内容。
        with open(filepath) as f:
            file_contents = f.read()
        # Split the file contents into smaller pieces if they exceed the max length.
        # 如果文件内容超过了指定的最大长度，将文件内容分成更小的片段。
        st = split_text(file_contents, max_length=split_text_max_length)
        # Determine whether the content is in latex format or plain text format.
        # 确定内容是latex格式还是普通文本格式。
        if latex:
            pretext_piece = "latex text"
        else:
            pretext_piece = "text"
        # Define a pretext for the translation message.
        # 定义翻译消息的前文。
        pretext = "Translate the following " + original_language + pretext_piece + " to " + target_language + latex + ":\n"
        # Initialize an empty list to store the translation history.
        # 初始化一个空列表以存储翻译历史。
        translation_history = []

        tmp_file_name = ''
        if write_tmp:
            if latex:
                file_type = '.tex'
            else:
                file_type = '.txt'
            now = datetime.datetime.now()
            tmp_file_name = 'tmp_' + now.strftime("%Y-%m-%d-%H%M%S") + file_type
            with open(tmp_file_name, 'w') as f:
                f.write('')

        # Translate each piece of the file contents and append the conversation history to the translation history list.
        # 逐个翻译文件内容的每一部分，并将对话历史附加到翻译历史列表中。
        for piece in st:
            next_message = pretext + piece
            print("Question：\n", next_message, "\n -------------------------------------------")
            responses = self.continue_conversation(next_message)
            translation_history = translation_history + responses
            if write_tmp:
                for response in responses:
                    with open(tmp_file_name, 'a') as f:
                        f.write(response['choices'][0]['message']['content'])

            for response in responses:
                print("Answer：\n", response['choices'][0]['message']['content'],
                      "\n -------------------------------------------")

        return translation_history

    @staticmethod
    def write_to_file(translation_history, output_file):
        # Write the translated content to an output file.
        # 将翻译后的内容写入输出文件。
        with open(output_file, 'w') as f:
            for response in translation_history:
                if response['choices'][0]['message']['role'] == 'assistant':
                    content = response['choices'][0]['message']['content']
                    f.write(content)
                f.write("\n")

    class MaxInputTokenExceededError(Exception):
        pass

    class UnKnownOpenAIError(Exception):
        pass

    def get_last_response(self):
        return self.history[-1]

    def get_last_response_content(self):
        return self.messages[-1]['content']

    def clear_all_history_and_massages(self):
        self.history = []
        self.messages = []
