from langgraph.graph import MessagesState

class ExtractionState(MessagesState):
    pdf_path: str = ""
    pdf_text: str = ""
    extracted_fields: dict = {}
    fields_to_retry: list = []
    retry_count: int = 0
    attributes_to_extract: dict = {}
    final_output: dict = {}