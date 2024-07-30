import json
# 可能需要导入其他一些必要的模块
from Tools.PythonTool import ExcelAnalyser
# 加载环境变量
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
from langchain_core.prompts import PromptTemplate
from Agent.AutoGPT import AutoGPT
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from Tools import *
from Tools.PythonTool import ExcelAnalyser
from Agent.Action import Action
from langchain.tools.render import render_text_description
# 导入其他可能需要的模块或类
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
import re
tools = [
    document_qa_tool,
    document_generation_tool,
    email_tool,
    excel_inspection_tool,
    directory_inspection_tool,
    finish_placeholder,
    ExcelAnalyser(
        prompt_file="./prompts/tools/excel_analyser.txt",
        verbose=True
    ).as_tool()
]

rendered_tools_description = render_text_description(tools)
main_prompt_file: str = "./prompts/main/main.txt"
work_dir: str = "./data"
output_parser = PydanticOutputParser(pydantic_object=Action)
def __chinese_friendly(string) -> str:
    lines = string.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('{') and line.endswith('}'):
            try:
                lines[i] = json.dumps(json.loads(line), ensure_ascii=False)
            except:
                pass
    return '\n'.join(lines)

main_prompt = PromptTemplate.from_file(
main_prompt_file
).partial(
    work_dir=work_dir,
    tools=rendered_tools_description,
    format_instructions=__chinese_friendly(
        output_parser.get_format_instructions(),
    )
)
# 定义要写入的文件名
output_file = 'tools_description.txt'

# 打开文件进行写入
with open(output_file, 'w', encoding='utf-8') as file:
    file.write("Rendered Tools Description:\n")
    file.write(rendered_tools_description)


