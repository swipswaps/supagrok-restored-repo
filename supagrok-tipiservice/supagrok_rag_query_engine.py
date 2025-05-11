#!/usr/bin/env python3
# PRF-SUPAGROK-RAGQUERYENGINE-2025-05-10
# UUID: queryeng-e5f6a7b8-c9d0-1234-5678-90abcdef
# Timestamp: 2025-05-10T19:30:00Z
# Last Modified: 2025-05-10T20:00:00Z 
# Description: (supagrok_rag_system_v2_final/supagrok_rag_query_engine.py) Handles querying the RAG vector index using LlamaIndex.
# Dependencies: Python packages: llama_index.core. Uses supagrok_rag_vector_store, supagrok_rag_config.
# Inputs: Query string, LlamaIndex VectorStoreIndex object (optional).
# Outputs: Query response string.
# Version: 1.2.1
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import logging
from pathlib import Path 
from typing import Optional as TypingOptional
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.response.schema import RESPONSE_TYPE as LlamaResponseType 

import supagrok_rag_vector_store 
import supagrok_rag_config

logger = logging.getLogger(__name__)

def get_query_engine(index_instance: TypingOptional[VectorStoreIndex] = None) -> TypingOptional[BaseQueryEngine]:
    """
    Returns a LlamaIndex query engine from the given index.
    """
    try:
        supagrok_rag_config.ensure_openai_api_key()
    except ValueError as e_apikey_qe:
        logger.error(f"Cannot create query engine due to API key configuration issue: {e_apikey_qe}")
        return None 

    current_loaded_index = index_instance
    if current_loaded_index is None:
        logger.info("No index instance provided to get_query_engine; attempting to load default persisted index.")
        current_loaded_index = supagrok_rag_vector_store.load_persisted_index()

    if current_loaded_index is None:
        logger.error("Failed to obtain or load a LlamaIndex VectorStoreIndex. Query engine cannot be created.")
        return None

    logger.info("Creating LlamaIndex query engine from the loaded/provided index...")
    try:
        query_engine_instance = current_loaded_index.as_query_engine(
            similarity_top_k=3, 
            streaming=False     
        ) 
        logger.info("LlamaIndex query engine created successfully.")
        return query_engine_instance
    except Exception as e_create_qe:
        logger.error(f"Failed to create LlamaIndex query engine from index: {e_create_qe}", exc_info=True)
        return None

def execute_query(query_text: str, query_engine_instance: TypingOptional[BaseQueryEngine] = None) -> TypingOptional[str]:
    """
    Executes a query using the provided LlamaIndex query engine.
    """
    active_query_engine_instance = query_engine_instance
    if active_query_engine_instance is None:
        logger.info("No query engine instance provided to execute_query; attempting to create one.")
        active_query_engine_instance = get_query_engine() 

    if active_query_engine_instance is None:
        logger.error("Cannot execute query: LlamaIndex query engine is unavailable or could not be initialized.")
        return "Error: Query engine unavailable. Please check data ingestion status and API key configuration."

    if not query_text or not query_text.strip():
        logger.warning("Query text is empty or contains only whitespace. Returning an empty response indication.")
        return "Query was empty. Please provide a valid question."

    logger.info(f"Executing query: '{query_text}'")
    try:
        response_object: LlamaResponseType = active_query_engine_instance.query(query_text)
        logger.info("Query executed successfully by LlamaIndex.")
        return str(response_object.response) if hasattr(response_object, 'response') else str(response_object)
    except Exception as e_exec_query:
        logger.error(f"Error during LlamaIndex query execution: {e_exec_query}", exc_info=True)
        error_string_upper = str(e_exec_query).upper()
        if "API KEY" in error_string_upper or "AUTHENTICATIONERROR" in error_string_upper or "RATE LIMIT" in error_string_upper:
            return f"Error during query (API issue likely: check key, quota, model access permissions): {e_exec_query}"
        return f"Error during query execution: {e_exec_query}"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) 
    logger.info("Supagrok Query Engine module self-test initiated.")
    
    try:
        logger.info("LlamaIndex Settings should be configured. Attempting to get query engine for self-test.")
        
        test_index_storage_path_for_qe = Path.cwd() / "test_rag_storage_v2_final_vs" 
        logger.info(f"Attempting to load index from: {test_index_storage_path_for_qe} for query engine self-test.")
        
        test_index_instance_for_qe = supagrok_rag_vector_store.load_persisted_index(persist_dir_override=test_index_storage_path_for_qe)

        if test_index_instance_for_qe:
            query_engine_for_self_test = get_query_engine(index_instance=test_index_instance_for_qe)
            if query_engine_for_self_test:
                sample_test_query = "What does the fox do?" 
                logger.info(f"Attempting self-test query: '{sample_test_query}'")
                query_answer = execute_query(sample_test_query, query_engine_for_self_test)
                logger.info(f"Self-Test Query Answer: {query_answer}")
            else:
                logger.error("Could not create query engine from the test index for self-testing.")
        else:
            logger.warning(f"Could not load test index from '{test_index_storage_path_for_qe}' for query engine self-test. Please run the vector_store.py self-test first to create it.")
            
    except ValueError as ve_qe_test: 
        logger.error(f"Query Engine Self-Test FAILED due to configuration error (likely API key for LlamaIndex Settings): {ve_qe_test}")
    except Exception as e_qe_test: 
        logger.error(f"An unexpected error occurred during query engine self-test: {e_qe_test}", exc_info=True)
        
    logger.info("Supagrok Query Engine module self-test finished.")
