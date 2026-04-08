from langchain_core.prompts import PromptTemplate

single_field_extraction_prompt = """You are a contract analysis expert. Your task is to extract the value for a specific field.
Field Name: {field_name}
Field Description: {field_desc}

Context:
{retrieved_context}

Extract the exact value from the context. If it is not present, return None."""

retry_field_extraction_prompt = """You are a contract analysis expert. Your task is to extract the value for a specific field.
Field Name: {field_name}
Field Description: {field_desc}

Context:
{retrieved_context}

Extract the exact value from the context. Be precise. If it is not present, return None."""
