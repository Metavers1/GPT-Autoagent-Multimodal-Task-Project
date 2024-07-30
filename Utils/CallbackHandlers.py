from typing import Optional, Union, Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import GenerationChunk, ChatGenerationChunk, LLMResult

from Utils.PrintUtils import *


class ColoredPrintHandler(BaseCallbackHandler):
    def __init__(self, color: str):
        BaseCallbackHandler.__init__(self)
        self._color = color

    def on_llm_new_token(
            self,
            token: str,
            *,
            chunk: Optional[Union[GenerationChunk, ChatGenerationChunk]] = None,
            run_id: UUID,
            parent_run_id: Optional[UUID] = None,
            **kwargs: Any,
    ) -> Any:
        color_print(token, self._color, end="")
        return token

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        color_print("\n", self._color, end="")
        return response