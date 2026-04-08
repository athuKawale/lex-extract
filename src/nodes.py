import os
import glob
import concurrent.futures
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import create_model
from typing import Optional

from src.state import ExtractionState
from src.schema import SharePurchaseAgreement
from src.tools import search_child_chunks
from src.prompt import single_field_extraction_prompt, retry_field_extraction_prompt
from src.utils.chat_model import llm
from src.utils.pdf_to_markdown import pdfs_to_markdowns
from src.utils.document_indexing import init_collection, index_documents



def ingest_node(state: ExtractionState):
    """Load PDF with pymupdf4llm, chunk + embed to Qdrant"""
    print(f"\n[INGEST_NODE] Processing PDF at {state.get('pdf_path', 'default')}")
    
    # 1. Convert to Markdown
    pdfs_to_markdowns(path_pattern=state.get("pdf_path"), overwrite=True)
    
    # 2. Init Qdrant Collection and Index
    init_collection()
    index_documents()
    
    full_text = ""
    md_files = glob.glob("markdown_output/*.md")
    if md_files:
        with open(md_files[0], "r", encoding="utf-8") as f:
            full_text = f.read()
    
    return {"pdf_text": full_text}

def _extract_single_field(field_name: str, field_desc: str, config: RunnableConfig, state: ExtractionState = None) -> tuple[str, str]:
    """Helper to query the vector store and extract a single field."""
    # 1. Targeted Retrieval
    query = f"Find information regarding: {field_name}. {field_desc}"
    retrieved_context = search_child_chunks.invoke({"query": query, "limit": 3})
    
    if state and state.get("pdf_text"):
        header_context = "--- DOCUMENT PREAMBLE / HEADER ---\n" + state["pdf_text"][:1500] + "\n\n--- SEMANTIC SEARCH CONTEXT ---\n"
        retrieved_context = header_context + retrieved_context
    
    # 2. Targeted LLM Extraction
    field_model = create_model(
        'DynamicExtraction',
        extracted_value=(str | None, ...)
    )
    
    parser = JsonOutputParser(pydantic_object=field_model)
    
    prompt = PromptTemplate(
        template=single_field_extraction_prompt + "\n\n{format_instructions}",
        input_variables=["field_name", "field_desc", "retrieved_context"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    result = chain.invoke({
        "field_name": field_name,
        "field_desc": field_desc,
        "retrieved_context": retrieved_context
    }, config=config)
    
    value = result.get("extracted_value") if isinstance(result, dict) else None
    
    print(f"  -> Extracted '{field_name}': {value}")
    return field_name, value

def extract_node(state: ExtractionState, config: RunnableConfig):
    """For each field, perform a deterministic targeted query & extraction."""
    print("\n[EXTRACT_NODE] Starting deterministic targeted extraction...")
    
    fields = SharePurchaseAgreement.model_fields
    mode = os.getenv("EXTRACTION_MODE", "sequential").lower()
    
    results = {}
    
    if mode == "parallel":
        print("[EXTRACT_NODE] Running in parallel mode (ThreadPoolExecutor)")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_field = {
                executor.submit(_extract_single_field, name, info.description, config, state): name 
                for name, info in fields.items()
            }
            for future in concurrent.futures.as_completed(future_to_field):
                name, val = future.result()
                results[name] = val
    else:
        print("[EXTRACT_NODE] Running in sequential mode")
        for name, info in fields.items():
            _, val = _extract_single_field(name, info.description, config, state)
            results[name] = val

    print(f"[EXTRACT_NODE] Initial extraction complete.\n")
    return {"extracted_fields": results, "retry_count": 0}


def validate_node(state: ExtractionState):
    """Check for None values, route to retry if needed"""
    print("\n[VALIDATE_NODE] Validating extracted fields...")
    
    extracted = state.get("extracted_fields", {})
    missing_fields = []
    
    for key, value in extracted.items():
        if value is None or value == "":
            missing_fields.append(key)
            
    if missing_fields:
        print(f"[VALIDATE_NODE] Missing fields detected: {missing_fields}")
    else:
        print("[VALIDATE_NODE] All fields found successfully.")
        
    return {"fields_to_retry": missing_fields}


def retry_node(state: ExtractionState, config: RunnableConfig):
    """Re-retrieve and re-extract only for missing fields."""
    retry_count = state.get("retry_count", 0) + 1
    missing_fields = state.get("fields_to_retry", [])
    print(f"\n[RETRY_NODE] Attempt {retry_count}. Retrying missing fields: {missing_fields}")
    
    fields = SharePurchaseAgreement.model_fields
    mode = os.getenv("EXTRACTION_MODE", "sequential").lower()
    
    current_fields = state.get("extracted_fields", {}).copy()
    retries = {}
    
    def _retry_single_field(field_name, field_desc, config, state=None):
        query = f"Identify any details discussing the {field_name}. {field_desc}"
        retrieved_context = search_child_chunks.invoke({"query": query, "limit": 5})
        
        if state and state.get("pdf_text"):
            header_context = "--- DOCUMENT PREAMBLE / HEADER ---\n" + state["pdf_text"][:1500] + "\n\n--- SEMANTIC SEARCH CONTEXT ---\n"
            retrieved_context = header_context + retrieved_context
        
        field_model = create_model(
            'DynamicExtraction',
            extracted_value=(str | None, ...)
        )
        
        parser = JsonOutputParser(pydantic_object=field_model)
        
        prompt = PromptTemplate(
            template=retry_field_extraction_prompt + "\n\n{format_instructions}",
            input_variables=["field_name", "field_desc", "retrieved_context"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = prompt | llm | parser

        result = chain.invoke({
            "field_name": field_name,
            "field_desc": field_desc,
            "retrieved_context": retrieved_context
        }, config=config)
        
        val = result.get("extracted_value") if isinstance(result, dict) else None
        return field_name, val

    if mode == "parallel":
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_field = {
                executor.submit(_retry_single_field, name, fields[name].description, config, state): name 
                for name in missing_fields if name in fields
            }
            for future in concurrent.futures.as_completed(future_to_field):
                name, val = future.result()
                if val:
                    print(f"  -> Successfully retrieved missing field: '{name}'")
                retries[name] = val
    else:
        for name in missing_fields:
            if name in fields:
                _, val = _retry_single_field(name, fields[name].description, config, state)
                if val:
                    print(f"  -> Successfully retrieved missing field: '{name}'")
                retries[name] = val

    for k, v in retries.items():
        if v:
            current_fields[k] = v
            
    return {"extracted_fields": current_fields, "retry_count": retry_count}


def output_node(state: ExtractionState):
    """Compile final JSON"""
    print("\n[OUTPUT_NODE] Finalizing extraction...")
    return {"final_output": state.get("extracted_fields", {})}