#!/usr/bin/env python3
# PRF-SUPAGROK-RAGQUERYENGINE-2025-05-10
# UUID: 4e5f7a9b-1c3d-55e6-f7a8-b9c0d1e2f3g4
# Timestamp: 2025-05-10T16:20:00Z
# Last Modified: 2025-05-10T18:10:00Z # Ensuring latest version for re-emission
# Description: (supagrok_rag_system_v2/supagrok_rag_query_engine.py) Handles querying the RAG vector index using LlamaIndex.
# Dependencies: Python packages: llama_index.core. Uses supagrok_rag_vector_store, supagrok_rag_config.
# Inputs: Query string, LlamaIndex VectorStoreIndex object (optional).
# Outputs: Query response string.
# Version: 1.1.1
# Author: SupagrokAgent/1.4
# PRF-Codex-Version: 1.6

import logging
from typing import Optional as TypingOptional
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.response.schema import RESPONSE_TYPE as LLAMA_RESPONSE_TYPE

import supagrok_rag_vector_store 
import supagrok_rag_config

logger = logging.getLogger(__name__)

def get_query_engine(index_instance: TypingOptional[VectorStoreIndex] = None) -> TypingOptional[BaseQueryEngine]:
    """
    Returns a LlamaIndex query engine.
    """
    try:
        supagrok_rag_config.ensure_openai_api_key()
    except ValueError as e:
        logger.error(f"Cannot create query engine due to API key configuration issue: {e}")
        return None 

    current_index = index_instance
    if current_index is None:
        logger.info("No index provided to get_query_engine; attempting to load default persisted index.")
        current_index = supagrok_rag_vector_store.load_persisted_index()

    if current_index is None:
        logger.error("Failed to obtain or load an index. Query engine cannot be created.")
        logger.error("Ensure documents have been ingested ('ingest' command) and the index is accessible.")
        return None

    logger.info("Creating query engine from the loaded/provided index...")
    try:
        query_engine_instance = current_index.as_query_engine(
            similarity_top_k=3, 
            streaming=False     
        ) 
        logger.info("Query engine created successfully.")
        return query_engine_instance
    except Exception as e:
        logger.error(f"Failed to create query engine from index: {e}", exc_info=True)
        return None

def execute_query(query_text: str, query_engine_instance: TypingOptional[BaseQueryEngine] = None) -> TypingOptional[str]:
    """
    Executes a query using the provided query engine.
    """
    active_query_engine = query_engine_instance
    if active_query_engine is None:
        logger.info("No query engine provided to execute_query; attempting to create one.")
        active_query_engine = get_query_engine() 

    if active_query_engine is None:
        logger.error("Cannot execute query: Query engine is unavailable or could not be initialized.")
        return "Error: Query engine unavailable. Check ingestion and API key configuration."

    if not query_text or not query_text.strip():
        logger.warning("Query text is empty. Returning empty response.")
        return "Query was empty."

    logger.info(f"Executing query: '{query_text}'")
    try:
        response: LLAMA_RESPONSE_TYPE = active_query_engine.query(query_text)
        logger.info("Query executed successfully.")
        return str(response.response) if hasattr(response, 'response') else str(response)
    except Exception as e:
        logger.error(f"Error during query execution: {e}", exc_info=True)
        err_str = str(e).upper()
        if "API KEY" in err_str or "AUTHENTICATION" in err_str or "RATE LIMIT" in err_str:
            return f"Error during query (API issue likely: check key, quota, model access): {e}"
        return f"Error during query execution: {e}"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Query Engine module self-test initiated.")
    
    try:
        logger.info("LlamaIndex Settings should be configured. Attempting to get query engine.")
        
        test_index_storage_path = Path.cwd() / "test_rag_storage_v2_vs" # From vector_store test
        test_index_instance = supagrok_rag_vector_store.load_persisted_index(persist_dir_override=test_index_storage_path)

        if test_index_instance:
            q_engine_for_test = get_query_engine(index_instance=test_index_instance)
            if q_engine_for_test:
                test_query_text = "What does the fox do?"
                logger.info(f"Attempting self-test query: '{test_query_text}'")
                answer = execute_query(test_query_text, q_engine_for_test)
                logger.info(f"Self-Test Query Answer: {answer}")
            else:
                logger.error("Could not create query engine from test index for self-testing.")
        else:
            logger.warning(f"Could not load test index from '{test_index_storage_path}' for query engine self-test. Run vector_store test first.")
            
    except ValueError as ve:
        logger.error(f"Query Engine Self-Test FAILED due to configuration error (likely API key for LlamaIndex Settings): {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during query engine self-test: {e}", exc_info=True)
        
    logger.info("Query Engine module self-test finished.")
