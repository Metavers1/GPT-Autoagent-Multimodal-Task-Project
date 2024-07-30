import pandas as pd


def get_sheet_names(
        filename: str
) -> str:
    """获取 Excel 文件的工作表名称"""
    excel_file = pd.ExcelFile(filename)
    sheet_names = excel_file.sheet_names
    return f"这是 '{filename}' 文件的工作表名称：\n\n{sheet_names}"

'''get_sheet_names 函数

目的：获取并返回一个 Excel 文件中所有工作表（sheet）的名称。
逻辑：
使用 pandas 库的 ExcelFile 类来加载 Excel 文件。
通过 sheet_names 属性获取所有工作表的名称。
将获取到的工作表名称格式化为字符串，并返回。'''

def get_column_names(
        filename: str
) -> str:
    """获取 Excel 文件的列名"""

    # 读取 Excel 文件的第一个工作表
    df = pd.read_excel(filename, sheet_name=0)  # sheet_name=0 表示第一个工作表

    column_names = '\n'.join(
        df.columns.to_list()
    )

    result = f"这是 '{filename}' 文件第一个工作表的列名：\n\n{column_names}"
    return result
'''使用 df.columns.to_list() 获取该工作表的所有列名，并将它们转换为列表。
将列名列表转换为字符串形式，并返回。'''

def get_first_n_rows(
        filename: str,
        n: int = 3
) -> str:
    """获取 Excel 文件的前 n 行"""

    result = get_sheet_names(filename) + "\n\n"

    result += get_column_names(filename) + "\n\n"

    # 读取 Excel 文件的第一个工作表
    df = pd.read_excel(filename, sheet_name=0)  # sheet_name=0 表示第一个工作表

    n_lines = '\n'.join(
        df.head(n).to_string(index=False, header=True).split('\n')
    )

    result += f"这是 '{filename}' 文件第一个工作表的前{n}行样例：\n\n{n_lines}"
    return result
# 指定文件路径
filename = r'C:\Users\w1462\Desktop\autogpt\auto-gpt-work\data\2023年8月-9月销售记录.xlsx'

