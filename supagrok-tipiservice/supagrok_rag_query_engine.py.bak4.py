#!/usr/bin/env python3
# PRF-SUPAGROK-RAGQUERYENGINE-2025-05-10
# UUID: queryeng-e5f6a7b8-c9d0-1234-5678-90abcdef
# Timestamp: 2025-05-10T19:30:00Z
# Last Modified: 2025-05-10T19:30:00Z 
# Description: (supagrok_rag_system_v2_final/supagrok_rag_query_engine.py) Handles querying the RAG vector index using LlamaIndex.
# Dependencies: Python packages: llama_index.core. Uses supagrok_rag_vector_store, supagrok_rag_config.
# Inputs: Query string, LlamaIndex VectorStoreIndex object (optional).
# Outputs: Query response string.
# Version: 1.2.0
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import logging
from pathlib import Path # For __main__ test path
from typing import Optional as TypingOptional
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.response.schema import RESPONSE_TYPE as LlamaResponseType # Alias for clarity

# Import our custom modules.
# The import of supagrok_rag_vector_store is critical as it initializes LlamaIndex Settings (LLM, Embed model).
# If LlamaIndex Settings fail there (e.g., API key issue), this module might fail to import or its functions will fail.
import supagrok_rag_vector_store 
import supagrok_rag_config

logger = logging.getLogger(__name__)

def get_query_engine(index_instance: TypingOptional[VectorStoreIndex] = None) -> TypingOptional[BaseQueryEngine]:
    """
    Returns a LlamaIndex query engine from the given index.
    If no index_instance is provided, it attempts to load the default persisted index.
    Relies on LlamaIndex Settings being configured globally via supagrok_rag_vector_store.py.
    """
    # API key validity for the LLM is critical. The LlamaIndex Settings block in vector_store
    # (imported above) should have already validated this. A direct check here can be for defense-in-depth.
    try:
        supagrok_rag_config.ensure_openai_api_key()
    except ValueError as e_apikey_qe:
        logger.error(f"Cannot create query engine due to API key configuration issue: {e_apikey_qe}")
        return None # Or raise, to be caught by the CLI or calling function

    current_loaded_index = index_instance
    if current_loaded_index is None:
        logger.info("No index instance provided to get_query_engine; attempting to load default persisted index.")
        current_loaded_index = supagrok_rag_vector_store.load_persisted_index()

    if current_loaded_index is None:
        logger.error("Failed to obtain or load a LlamaIndex VectorStoreIndex. Query engine cannot be created.")
        logger.error("Please ensure documents have been ingested using the 'ingest' command and the index is accessible at the configured storage path.")
        return None

    logger.info("Creating LlamaIndex query engine from the loaded/provided index...")
    try:
        # The query engine will use the LLM and embedding model from global LlamaIndex Settings.
        # We can customize query engine parameters here if needed, e.g.:
        # similarity_top_k: Number of top similar nodes to retrieve.
        # response_mode: How LlamaIndex synthesizes the response (e.g., "refine", "tree_summarize").
        query_engine_instance = current_loaded_index.as_query_engine(
            similarity_top_k=3, # Retrieve top 3 most similar nodes from the vector store
            streaming=False     # Set to True for token-wise streaming output if the application supports it
        ) 
        logger.info("LlamaIndex query engine created successfully.")
        return query_engine_instance
    except Exception as e_create_qe:
        logger.error(f"Failed to create LlamaIndex query engine from index: {e_create_qe}", exc_info=True)
        return None

def execute_query(query_text: str, query_engine_instance: TypingOptional[BaseQueryEngine] = None) -> TypingOptional[str]:
    """
    Executes a query using the provided LlamaIndex query engine.
    If no query_engine_instance is provided, attempts to create one using the default persisted index.
    """
    active_query_engine_instance = query_engine_instance
    if active_query_engine_instance is None:
        logger.info("No query engine instance provided to execute_query; attempting to create one.")
        active_query_engine_instance = get_query_engine() # This will try to load the default index

    if active_query_engine_instance is None:
        logger.error("Cannot execute query: LlamaIndex query engine is unavailable or could not be initialized.")
        return "Error: Query engine unavailable. Please check data ingestion status and API key configuration."

    if not query_text or not query_text.strip():
        logger.warning("Query text is empty or contains only whitespace. Returning an empty response indication.")
        return "Query was empty. Please provide a valid question."

    logger.info(f"Executing query: '{query_text}'")
    try:
        # The query method returns a RESPONSE object from LlamaIndex
        response_object: LlamaResponseType = active_query_engine_instance.query(query_text)
        logger.info("Query executed successfully by LlamaIndex.")
        # The actual text response is usually in response_object.response
        # response_object.source_nodes can be inspected for retrieved context
        return str(response_object.response) if hasattr(response_object, 'response') else str(response_object)
    except Exception as e_exec_query:
        logger.error(f"Error during LlamaIndex query execution: {e_exec_query}", exc_info=True)
        # Provide more context if it's a common API-related error
        error_string_upper = str(e_exec_query).upper()
        if "API KEY" in error_string_upper or "AUTHENTICATIONERROR" in error_string_upper or "RATE LIMIT" in error_string_upper:
            return f"Error during query (API issue likely: check key, quota, model access permissions): {e_exec_query}"
        return f"Error during query execution: {e_exec_query}"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Set logging for __main__ tests
    logger.info("Supagrok Query Engine module self-test initiated.")
    
    # This test relies on an index potentially created by supagrok_rag_vector_store.py's __main__ block
    # in its test directory (e.g., 'test_rag_storage_v2_final_vs').
    # It also requires a valid OpenAI API key for LlamaIndex Settings.
    try:
        # API key check is implicitly handled by LlamaIndex Settings in vector_store import
        logger.info("LlamaIndex Settings should be configured. Attempting to get query engine for self-test.")
        
        # Attempt to load the index specifically created by vector_store's test for a consistent test
        test_index_storage_path_for_qe = Path.cwd() / "test_rag_storage_v2_final_vs" # Matches vector_store's test dir
        logger.info(f"Attempting to load index from: {test_index_storage_path_for_qe} for query engine self-test.")
        
        test_index_instance_for_qe = supagrok_rag_vector_store.load_persisted_index(persist_dir_override=test_index_storage_path_for_qe)

        if test_index_instance_for_qe:
            query_engine_for_self_test = get_query_engine(index_instance=test_index_instance_for_qe)
            if query_engine_for_self_test:
                sample_test_query = "What does the fox do?" # Query related to vector_store's dummy docs
                logger.info(f"Attempting self-test query: '{sample_test_query}'")
                query_answer = execute_query(sample_test_query, query_engine_for_self_test)
                logger.info(f"Self-Test Query Answer: {query_answer}")
            else:
                logger.error("Could not create query engine from the test index for self-testing.")
        else:
            logger.warning(f"Could not load test index from '{test_index_storage_path_for_qe}' for query engine self-test. Please run the vector_store.py self-test first to create it.")
            
    except ValueError as ve_qe_test: # Catch API key error from config or LlamaIndex Settings
        logger.error(f"Query Engine Self-Test FAILED due to configuration error (likely API key for LlamaIndex Settings): {ve_qe_test}")
    except Exception as e_qe_test: # Catch any other unexpected error
        logger.error(f"An unexpected error occurred during query engine self-test: {e_qe_test}", exc_info=True)
        
    logger.info("Supagrok Query Engine module self-test finished.")
