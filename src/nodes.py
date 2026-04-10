import os
import glob
import concurrent.futures
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import create_model
from typing import Optional

from src.state import ExtractionState
from src.tools import search_child_chunks
from src.prompt import single_field_extraction_prompt, retry_field_extraction_prompt
from src.utils.chat_model import llm
from src.utils.pdf_to_markdown import pdfs_to_markdowns
from src.utils.document_indexing import init_collection, index_documents



from src.utils.cache_manager import get_file_hash, is_file_processed, update_cache_registry

def ingest_node(state: ExtractionState):
    """Load PDF with pymupdf4llm, chunk + embed to Qdrant"""
    pdf_path = state.get("pdf_path")
    filename = os.path.basename(pdf_path)
    
    print(f"\n[INGEST_NODE] Checking cache for {filename}")
    
    file_hash = get_file_hash(pdf_path)
    
    if is_file_processed(filename, file_hash):
        print(f"[INGEST_NODE] Document {filename} already indexed. Skipping ingestion.")
        # Load existing full text from markdown
        md_path = os.path.join("markdown_output", f"{Path(filename).stem}.md")
        full_text = ""
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                full_text = f.read()
        return {"pdf_text": full_text}

    print(f"[INGEST_NODE] Processing new/modified PDF: {filename}")
    
    # 1. Convert to Markdown
    pdfs_to_markdowns(path_pattern=pdf_path, overwrite=False)
    
    # 2. Init Qdrant Collection (Incremental) and Index only this file
    init_collection(force_recreate=False)
    index_documents(specific_files=[filename])
    
    # Update registry
    update_cache_registry(filename, file_hash)
    
    full_text = ""
    md_path = os.path.join("markdown_output", f"{Path(filename).stem}.md")
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            full_text = f.read()
    
    return {"pdf_text": full_text}

def _extract_single_field(field_name: str, field_desc: str, config: RunnableConfig, state: ExtractionState = None) -> tuple[str, str]:
    """Helper to query the vector store and extract a single field."""
    query = f"Find information regarding: {field_name}. {field_desc}"
    
    file_name = None
    if state and state.get("pdf_path"):
        file_name = os.path.basename(state.get("pdf_path"))

    retrieved_context = search_child_chunks.invoke({
        "query": query, 
        "limit": 3,
        "file_name": file_name
    })
    
    if state and state.get("pdf_text"):
        header_context = "--- DOCUMENT PREAMBLE / HEADER ---\n" + state["pdf_text"][:1500] + "\n\n--- SEMANTIC SEARCH CONTEXT ---\n"
        retrieved_context = header_context + retrieved_context

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
    
    dynamic_attrs = state.get("attributes_to_extract", {})
    if not dynamic_attrs:
        print("[EXTRACT_NODE] No attributes provided to extract. Skipping.")
        return {"extracted_fields": {}, "retry_count": 0}

    fields_to_extract = dynamic_attrs

    mode = os.getenv("EXTRACTION_MODE", "sequential").lower()
    
    results = {}
    
    if mode == "parallel":
        print("[EXTRACT_NODE] Running in parallel mode (ThreadPoolExecutor)")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_field = {
                executor.submit(_extract_single_field, name, desc, config, state): name 
                for name, desc in fields_to_extract.items()
            }
            for future in concurrent.futures.as_completed(future_to_field):
                name, val = future.result()
                results[name] = val
    else:
        print("[EXTRACT_NODE] Running in sequential mode")
        for name, desc in fields_to_extract.items():
            _, val = _extract_single_field(name, desc, config, state)
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
    
    dynamic_attrs = state.get("attributes_to_extract", {})
    if not dynamic_attrs:
        print("[RETRY_NODE] No attributes provided to extract. Skipping.")
        return {"extracted_fields": state.get("extracted_fields", {}), "retry_count": retry_count}

    fields_to_extract = dynamic_attrs

    mode = os.getenv("EXTRACTION_MODE", "sequential").lower()
    
    current_fields = state.get("extracted_fields", {}).copy()
    retries = {}
    
    def _retry_single_field(field_name, field_desc, config, state=None):
        query = f"Identify any details discussing the {field_name}. {field_desc}"
        
        file_name = None
        if state and state.get("pdf_path"):
            file_name = os.path.basename(state.get("pdf_path"))
            
        retrieved_context = search_child_chunks.invoke({
            "query": query, 
            "limit": 5,
            "file_name": file_name
        })
        
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
                executor.submit(_retry_single_field, name, fields_to_extract[name], config, state): name 
                for name in missing_fields if name in fields_to_extract
            }
            for future in concurrent.futures.as_completed(future_to_field):
                name, val = future.result()
                if val:
                    print(f"  -> Successfully retrieved missing field: '{name}'")
                retries[name] = val
    else:
        for name in missing_fields:
            if name in fields_to_extract:
                _, val = _retry_single_field(name, fields_to_extract[name], config, state)
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