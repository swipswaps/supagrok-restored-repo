#!/usr/bin/env python3
# PRF-SUPAGROK-RAGQUERYENGINE-2025-05-09
# UUID: d4e5f6a7-b8c9-0123-4567-890abcdef012
# Timestamp: 2025-05-09T14:15:00Z
# Last Modified: 2025-05-09T14:15:00Z
# Description: /opt/supagrok/supagrok_rag_system/supagrok_rag_query_engine.py - Handles querying the RAG vector index.
# Dependencies: llama_index.core, logging, supagrok_rag_vector_store, supagrok_rag_config
# Inputs: Query string, LlamaIndex VectorStoreIndex object.
# Outputs: Query response string.
# Version: 1.0.0
# Author: SupagrokAgent/1.2
# PRF-Codex-Version: 1.4

import logging
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import BaseQueryEngine

# Assuming these modules are in the same directory or Python path
import supagrok_rag_vector_store
import supagrok_rag_config

logger = logging.getLogger(__name__)

def get_query_engine(index: Optional[VectorStoreIndex] = None) -> Optional[BaseQueryEngine]:
    """
    Returns a query engine from the given index.
    If no index is provided, it attempts to load the default persisted index.
    """
    try:
        supagrok_rag_config.ensure_openai_api_key() # Crucial for OpenAI LLM
    except ValueError as e:
        logger.error(f"Cannot proceed with query engine due to API key issue: {e}")
        return None

    if index is None:
        logger.info("No index provided, attempting to load default persisted index.")
        index = supagrok_rag_vector_store.load_persisted_index()

    if index is None:
        logger.error("Failed to get or load an index. Query engine cannot be created.")
        logger.error("Please ensure documents have been ingested first using the 'ingest' command.")
        return None

    logger.info("Creating query engine from index...")
    # You can customize the query engine here, e.g., similarity_top_k, response_mode
    # query_engine = index.as_query_engine(similarity_top_k=3, response_mode="compact")
    query_engine = index.as_query_engine(streaming=False) # Set streaming=True for token-wise output
    logger.info("Query engine created successfully.")
    return query_engine

def execute_query(query_text: str, query_engine: Optional[BaseQueryEngine] = None) -> Optional[str]:
    """
    Executes a query using the provided query engine.
    If no query engine is provided, attempts to create one from the default index.
    """
    if query_engine is None:
        logger.info("No query engine provided, attempting to create one.")
        query_engine = get_query_engine() # Will try to load default index

    if query_engine is None:
        logger.error("Cannot execute query: Query engine is not available.")
        return "Error: Query engine could not be initialized. Was data ingested?"

    logger.info(f"Executing query: {query_text}")
    try:
        response = query_engine.query(query_text)
        logger.info("Query executed successfully.")
        # The response object can be complex. We usually want response.response for the text.
        # If streaming, response is a StreamingResponse object.
        return str(response) # Ensure it's a string
    except Exception as e:
        logger.error(f"Error during query execution: {e}")
        return f"Error during query: {e}"

if __name__ == "__main__":
    # Example Usage (assumes an index has been created and persisted by supagrok_rag_vector_store.py example)
    logging.basicConfig(level=logging.INFO)
    
    logger.info("--- Testing Query Engine ---")
    
    # This test relies on the index created by supagrok_rag_vector_store.py's __main__ block
    # Ensure that script's __main__ was run first and 'test_rag_storage' exists.
    # For a standalone test, you'd need to ensure an index is present.
    
    # Test loading the index and creating a query engine
    test_index = supagrok_rag_vector_store.load_persisted_index(
        str(supagrok_rag_config.Path.cwd() / "test_rag_storage")
    )

    if test_index:
        q_engine = get_query_engine(index=test_index)
        if q_engine:
            test_query = "What fruits are mentioned in the documents?"
            logger.info(f"Attempting test query: {test_query}")
            answer = execute_query(test_query, q_engine)
            logger.info(f"Query Answer: {answer}")

            test_query_2 = "Tell me about apples."
            logger.info(f"Attempting test query: {test_query_2}")
            answer_2 = execute_query(test_query_2, q_engine) # Test without passing engine
            logger.info(f"Query Answer 2: {answer_2}")
        else:
            logger.error("Could not create query engine for testing.")
    else:
        logger.warning("Could not load 'test_rag_storage' index for query engine testing. Run vector_store example first.")
    
    logger.info("Query engine example finished.")

