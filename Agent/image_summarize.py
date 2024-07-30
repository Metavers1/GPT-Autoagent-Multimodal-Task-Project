import base64
import os

from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage
# 加载环境变量
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

#本文是用于 多模态RAG的 图像提取 ，提取成base64码和图像总结文本，用于多模态向量库的
def encode_image(image_path):
    """Getting the base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def image_summarize(img_base64, prompt):
    """Make image summary"""
    model =  ChatOpenAI(model="gpt-4-vision-preview",max_tokens=4096)

    msg = model(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                    },
                ]
            )
        ]
    )
    return msg.content

def generate_img_summaries(path):
    """
    Generate summaries and base64 encoded strings for images
    path: Path to list of .jpg files extracted by Unstructured
    """
    found_images = False

    # Store base64 encoded images
    img_base64_list = []

    # Store image summaries
    image_summaries = []

    # Prompt
    prompt = """You are an assistant tasked with summarizing images for retrieval. \
    These summaries will be embedded and used to retrieve the raw image. \
    Give a concise summary of the image that is well optimized for retrieval.用中文描述"""

    # 遍历目录中的文件
    for img_file in sorted(os.listdir(path)):
        if img_file.endswith(".png"):
            img_path = os.path.join(path, img_file)
            base64_image = encode_image(img_path)
            img_base64_list.append(base64_image)
            image_summaries.append(image_summarize(base64_image, prompt))
            # 找到图片文件时更新标志
            found_images = True

    # 如果没有找到任何图片文件，打印消息
    if not found_images:
        print("No images found.")

    return img_base64_list, image_summaries

fpath = "./Agent"
# Image summaries
img_base64_list, image_summaries = generate_img_summaries(fpath)
# 检查并打印 image_summaries 列表
if image_summaries:
    for summary in image_summaries:
        print(summary)
else:
    print("No summaries found.")