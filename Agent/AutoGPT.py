import json
from typing import List, Optional, Tuple

from langchain.memory.chat_memory import BaseChatMemory
from langchain.tools.render import render_text_description
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.memory import ConversationTokenBufferMemory, VectorStoreRetrieverMemory
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.schema.output_parser import StrOutputParser
from langchain.tools.base import BaseTool
from langchain.vectorstores.base import VectorStoreRetriever
from langchain_core.memory import BaseMemory
from langchain_core.prompts import PromptTemplate
from pydantic import ValidationError
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableLambda

from langchain_core.messages import HumanMessage
from Agent.Action import Action
import jinja2
from Utils.CallbackHandlers import *


class AutoGPT:
    """AutoGPT：基于Langchain实现"""

    @staticmethod
    def __chinese_friendly(string) -> str:
        lines = string.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('{') and line.endswith('}'):
                try:
                    lines[i] = json.dumps(json.loads(line), ensure_ascii=False)
                except:
                    pass
        return '\n'.join(lines)

    @staticmethod
    def __format_long_term_memory(task_description: str, memory: BaseChatMemory) -> str:
        return memory.load_memory_variables(
            {"prompt": task_description}
        )["history"]

    @staticmethod
    def __format_short_term_memory(memory: BaseChatMemory) -> str:
        messages = memory.chat_memory.messages
        string_messages = [messages[i].content for i in range(1, len(messages))]
        return "\n".join(string_messages)

    def __init__(
            self,
            llm: BaseChatModel,
            tools: List[BaseTool],
            work_dir: str = "./data",
            main_prompt_file: str = "./prompts/main/main.json",
            final_prompt_file: str = "./prompts/main/final_step.json",
            max_thought_steps: Optional[int] = 10,
            memery_retriever: Optional[VectorStoreRetriever] = None,
    ):
        self.llm = llm
        self.tools = tools
        self.work_dir = work_dir
        self.max_thought_steps = max_thought_steps
        self.memery_retriever = memery_retriever
        self.data_dict = {
            "context": {
                "images": []
            },
            "task_description": {},
            "short_term_memory": {},
            "long_term_memory": {}
        }
        self.use_final_prompt = False
        # OutputFixingParser： 如果输出格式不正确，尝试修复
        self.output_parser = PydanticOutputParser(pydantic_object=Action)
        self.robust_parser = OutputFixingParser.from_llm(parser=self.output_parser, llm=self.llm)

        self.main_prompt_file = main_prompt_file
        self.final_prompt_file = final_prompt_file

        self.__init_prompt_templates()
        self.__init_chains()

        self.verbose_handler = ColoredPrintHandler(color=THOUGHT_COLOR)

    def __init_prompt_templates(self):

        self.main_prompt = PromptTemplate.from_file(
            self.main_prompt_file,
        ).partial(
            work_dir=self.work_dir,
            tools=render_text_description(self.tools),
            format_instructions=self.__chinese_friendly(
                self.output_parser.get_format_instructions(),
            )
        )
        self.final_prompt = PromptTemplate.from_file(
            self.final_prompt_file, 
        )

    def __init_chains(self):
        # 主流程的chain
        #self.main_chain = (self.main_prompt | self.llm | StrOutputParser())
        self.main_chain = (RunnableLambda(self.handle_messages) | self.llm | StrOutputParser())
        # 最终一步的chain
        #self.final_chain = (self.final_prompt | self.llm | StrOutputParser())
        self.final_chain = (RunnableLambda(self.handle_messages) | self.llm | StrOutputParser())
        
    def handle_messages(self, data_dict):
        """
        Generate a structured message containing the prompt text and any additional elements like images.
        """
        
        # 使用 main_prompt 生成基于当前状态的文本
        if self.use_final_prompt:
            formatted_texts = self.final_prompt.format(**data_dict)
        else:
            formatted_texts = self.main_prompt.format(**data_dict)
       # print("data_dict之后的formatted_texts:", formatted_texts)
        messages = [{
            "type": "text",
            "text": (
                f"{formatted_texts}"
            )
        }]
        

        # # 检查是否有图片并添加到消息中
        # if "images" in data_dict.get("context", {}):
        #     for image in data_dict["context"]["images"]:
        #         image_message = {
        #             "type": "image_url",
        #             "image_url": {"url": f"data:image/jpeg;base64,{image}"}
        #         }
        #         messages.append(image_message)
                
                
                
        if "images" in data_dict.get("context", {}):
            with open('base64_images.txt', 'w') as file:  # 打开一个文本文件用于写入图像的 base64 编码
                for image in data_dict["context"]["images"]:
                    image_message = {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image}"}
                    }
                    messages.append(image_message)
                    file.write(image + '\n')  # 将base64编码写入文件，每个图像编码后跟一个换行符

            #print("Base64 encoded images have been written to 'base64_images.txt'")

        # 将所有消息以完整的 JSON 格式写入另一个文件

        with open('full_messages.json', 'w', encoding='utf-8') as msg_file:
            json.dump(messages, msg_file, ensure_ascii=False, indent=4)

       # print("Complete messages have been written to 'full_messages.json'")
        #print("Messages before sending:", messages)
        # for message in messages:
        #     if message['type'] == 'image_url':
        #         print("Found image with URL starting:", message['image_url']['url'][:30])
        #     else:
        #         print("Found text message")

        return [HumanMessage(content=messages)]



    def __find_tool(self, tool_name: str) -> Optional[BaseTool]:
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None

    def __step(self,
               task_description,
               short_term_memory,
               long_term_memory,data_dict,verbose=False) -> Tuple[Action, str]:
        """执行一步思考"""
        # 添加和格式化必要的信息到data_dict
        if 'task_description' in data_dict:
            data_dict['task_description'] = task_description
        if 'short_term_memory' in data_dict:
            data_dict['short_term_memory'] = self.__format_short_term_memory(short_term_memory)
        if 'long_term_memory' in data_dict:
            data_dict['long_term_memory'] = self.__format_long_term_memory(task_description, long_term_memory) if long_term_memory is not None else ""
            
        response = ''
        #print("Before invoking:", data_dict)
        # 使用invoke替代stream来获取响应
        response = self.main_chain.invoke(data_dict)
        
        if response is None or 'choices' not in response:
            raise ValueError("API调用未返回有效的响应或响应结构不符合预期")
        print("After invoking, response:", response)
        
        action = self.robust_parser.parse(response)
        # if verbose:
        #     print("思考过程 :", response)
        return action, response,data_dict

    def __final_step(self, short_term_memory, task_description,data_dict) -> str:
        """最后一步, 生成最终的输出"""
        self.use_final_prompt = True
        
        if 'task_description' in data_dict:
            data_dict['task_description'] = task_description
        if 'short_term_memory' in data_dict:
            data_dict['formatted_short_term_memory'] = self.__format_short_term_memory(short_term_memory)
            
        response = self.final_chain.invoke(data_dict)
        self.use_final_prompt = False
        
        return response

    def __exec_action(self, action: Action) -> str:
        # 查找工具
        tool = self.__find_tool(action.name)
        if tool is None:
            observation = (
                f"Error: 找不到工具或指令 '{action.name}'. "
                f"请从提供的工具/指令列表中选择，请确保按对顶格式输出。"
            )
        else:
            try:
                # 执行工具
                observation = tool.run(action.args)
            except ValidationError as e:
                # 工具的入参异常
                observation = (
                    f"Validation Error in args: {str(e)}, args: {action.args}"
                )
            except Exception as e:
                # 工具执行异常
                observation = f"Error: {str(e)}, {type(e).__name__}, args: {action.args}"

        return observation

    def __init_short_term_memory(self) -> BaseChatMemory:
        short_term_memory = ConversationTokenBufferMemory(
            llm=self.llm,
            max_token_limit=4000,
        )
        short_term_memory.save_context(
            {"input": "\n初始化"},
            {"output": "\n开始"}
        )
        return short_term_memory

    def __connect_long_term_memory(self) -> BaseMemory:
        if self.memery_retriever is not None:
            long_term_memory = VectorStoreRetrieverMemory(
                retriever=self.memery_retriever,
            )
        else:
            long_term_memory = None
        return long_term_memory

    @staticmethod
    def __update_short_term_memory(
            short_term_memory: BaseChatMemory,
            response: str,
            observation: str,
            
            
    ):
        short_term_memory.save_context(
            {"input": response},
            
            {"output": "\n此工具的返回结果:\n" + observation}
        )

    @staticmethod
    def __update_long_term_memory(
            long_term_memory: BaseMemory,
            task_description: str,
            final_reply: str
    ):
        if long_term_memory is not None:
            long_term_memory.save_context(
                {"input": task_description},
                {"output": final_reply}
            )

    @staticmethod
    def __show_observation(observation: str, verbose: bool):
        if verbose:
            color_print(f"----\n结果:\n{observation}", OBSERVATION_COLOR)

    def run(self, task_description, verbose=False) -> str:
        # 初始化短时记忆
        short_term_memory = self.__init_short_term_memory()
        # 连接长时记忆（如果有）
        long_term_memory = self.__connect_long_term_memory()

        # 思考步数
        thought_step_count = 0

        # 开始逐步思考
        while thought_step_count < self.max_thought_steps:
            if verbose:
                color_print(f">>>>Round: {thought_step_count}<<<<", ROUND_COLOR)

            # 执行一步思考
            action, response,data_dict = self.__step(
                task_description=task_description,
                short_term_memory=short_term_memory,
                long_term_memory=long_term_memory,data_dict=self.data_dict,verbose=True
            )
            self.data_dict =data_dict
            # 如果是结束指令，执行最后一步
            if action.name == "FINISH":
                break
            action_name =str(action.name)
            # 执行动作
            response += "\n本轮对话调用的工具为：{}".format(action_name)
            observation = self.__exec_action(action)
            # 检查observation类型，并相应处理
            if isinstance(observation, list):
                # 假设observation是图像的base64列表
                self.data_dict["context"]["images"].extend(observation)
                observation = "<image>"
                self.__update_short_term_memory(
                    short_term_memory, response, observation
                )
            else:
                # 如果observation是字符串，显示并继续处理
                self.__show_observation(observation, verbose)
                # 更新短时记忆
                self.__update_short_term_memory(
                    short_term_memory, response, observation
                )

            thought_step_count += 1

        if thought_step_count >= self.max_thought_steps:
            # 如果思考步数达到上限，返回错误信息
            reply = "抱歉，我没能完成您的任务。"
            self.data_dict = {
            "context": {
                "images": []
            },
            "task_description": {},
            "short_term_memory": {},
            "long_term_memory": {}
        }
        else:
            # 否则，执行最后一步
            
            reply = self.__final_step(short_term_memory, task_description,data_dict=self.data_dict)
            self.data_dict = {
            "context": {
                "images": []
            },
            "task_description": {},
            "short_term_memory": {},
            "long_term_memory": {}
        }
        # 更新长时记忆
        self.__update_long_term_memory(long_term_memory, task_description, reply)

        return reply
