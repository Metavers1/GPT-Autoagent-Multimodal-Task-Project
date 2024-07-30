from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Action(BaseModel):
    name: str = Field(description="工具或指令名称")
    args: Optional[Dict[str, Any]] = Field(description="工具或指令参数，由参数名称和参数值组成")
