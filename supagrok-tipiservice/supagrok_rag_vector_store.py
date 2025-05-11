#!/usr/bin/env python3
# PRF-SUPAGROK-RAGVECTORSTORE-2025-05-10
# UUID: vecstore-d4e5f6a7-b8c9-0123-4567-890abcde
# Timestamp: 2025-05-10T19:30:00Z
# Last Modified: 2025-05-10T20:00:00Z 
# Description: (supagrok_rag_system_v2_final/supagrok_rag_vector_store.py) Manages the LlamaIndex vector store for the RAG system.
# Dependencies: Python packages: llama_index.core, llama_index.llms.openai, llama_index.embeddings.huggingface. Uses supagrok_rag_config.
# Inputs: List of LlamaIndex Document objects for ingestion, storage path.
# Outputs: Creates/updates a vector index on disk. Loads an index from disk.
# Version: 1.2.1
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import logging
from pathlib import Path
from typing import List, Optional as TypingOptional

from llama_index.core import (
    Document,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings  
)
from llama_index.llms.openai import OpenAI 
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

import supagrok_rag_config 

logger = logging.getLogger(__name__)

try:
    supagrok_rag_config.ensure_openai_api_key() 
    
    Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1) 
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    logger.info(f"LlamaIndex global LLM successfully set to: {Settings.llm.metadata.model_name}")
    logger.info(f"LlamaIndex global Embedding model successfully set to: {Settings.embed_model.model_name}")

except ValueError as e_apikey: 
    logger.critical(f"CRITICAL FAILURE in LlamaIndex Settings: OpenAI API key issue: {e_apikey}")
    raise 
except Exception as e_settings: 
    logger.critical(f"CRITICAL FAILURE: Unexpected error configuring LlamaIndex Settings: {e_settings}", exc_info=True)
    raise


def create_and_persist_index(documents: List[Document], persist_dir_override: TypingOptional[Path] = None) -> VectorStoreIndex:
    """
    Creates a new vector index from the provided LlamaIndex Document objects and persists it to disk.
    """
    if not documents:
        logger.error("No documents provided for indexing. Aborting index creation.")
        raise ValueError("Cannot create an index from an empty list of documents.")

    persist_dir_actual = persist_dir_override if persist_dir_override else supagrok_rag_config.get_storage_path()
    persist_dir_actual.mkdir(parents=True, exist_ok=True) 
    
    logger.info(f"Creating/updating LlamaIndex vector index in: {persist_dir_actual} with {len(documents)} document(s).")
    logger.info(f"Using LLM: {Settings.llm.metadata.model_name} and Embed Model: {Settings.embed_model.model_name} from global LlamaIndex Settings.")

    try:
        index = VectorStoreIndex.from_documents(
            documents,
            show_progress=True, 
        )
        index.storage_context.persist(persist_dir=str(persist_dir_actual))
        logger.info(f"Successfully created/updated and persisted LlamaIndex vector index at {persist_dir_actual}.")
        return index
    except Exception as e_create_index:
        logger.error(f"Failed to create or persist LlamaIndex vector index at {persist_dir_actual}: {e_create_index}", exc_info=True)
        raise 

def load_persisted_index(persist_dir_override: TypingOptional[Path] = None) -> TypingOptional[VectorStoreIndex]:
    """
    Loads an existing LlamaIndex vector index from the specified persistence directory.
    """
    persist_dir_actual = persist_dir_override if persist_dir_override else supagrok_rag_config.get_storage_path()

    if not persist_dir_actual.exists() or not any(persist_dir_actual.iterdir()): 
        logger.warning(f"LlamaIndex persistence directory {persist_dir_actual} does not exist or is empty. Cannot load index.")
        return None

    logger.info(f"Attempting to load LlamaIndex vector index from: {persist_dir_actual}")
    logger.info(f"Using LLM: {Settings.llm.metadata.model_name} and Embed Model: {Settings.embed_model.model_name} from global LlamaIndex Settings for loading.")
    try:
        storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir_actual))
        index = load_index_from_storage(storage_context)
        logger.info(f"Successfully loaded LlamaIndex vector index from {persist_dir_actual}.")
        return index
    except FileNotFoundError: 
        logger.error(f"Core LlamaIndex index files not found in {persist_dir_actual}. Has an index been created and persisted here correctly?")
        return None
    except Exception as e_load_index:
        logger.error(f"Failed to load LlamaIndex vector index from {persist_dir_actual}: {e_load_index}", exc_info=True)
        logger.error("The stored index might be corrupted, incomplete, or incompatible. Consider re-ingesting documents.")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) 
    logger.info("Supagrok Vector Store module self-test initiated.")
    
    try:
        logger.info("Global LlamaIndex Settings should be configured by now (check logs above).")
        
        doc_vs_1 = Document(text="The quick brown fox jumps over the lazy dog. This is document one.")
        doc_vs_2 = Document(text="Lorem ipsum dolor sit amet, consectetur adipiscing elit. This is document two.")
        test_documents_for_vs = [doc_vs_1, doc_vs_2]

        test_storage_dir_for_vs = Path.cwd() / "test_rag_storage_v2_final_vs" 
        if test_storage_dir_for_vs.exists(): 
            import shutil
            shutil.rmtree(test_storage_dir_for_vs)
            logger.info(f"Cleaned up existing test storage directory: {test_storage_dir_for_vs}")

        logger.info("--- Testing LlamaIndex index creation and persistence ---")
        created_index_instance = create_and_persist_index(test_documents_for_vs, persist_dir_override=test_storage_dir_for_vs)
        if created_index_instance: 
            logger.info(f"Index created. Number of documents in docstore: {len(created_index_instance.docstore.docs)}")

        logger.info("--- Testing LlamaIndex index loading ---")
        loaded_index_instance = load_persisted_index(persist_dir_override=test_storage_dir_for_vs)
        if loaded_index_instance:
            logger.info(f"Index loaded. Number of documents in docstore: {len(loaded_index_instance.docstore.docs)}")
            query_engine_for_vs_test = loaded_index_instance.as_query_engine()
            test_query_response = query_engine_for_vs_test.query("What does the fox jump over?")
            logger.info(f"Test query response from loaded index: {test_query_response}")
        else:
            logger.warning("Could not load index for self-testing the vector store.")
            
    except ValueError as ve_vs_test: 
        logger.error(f"Vector Store Self-Test FAILED due to configuration error (likely API key for LlamaIndex Settings): {ve_vs_test}")
    except Exception as e_vs_test: 
        logger.error(f"An unexpected error occurred during vector store self-test: {e_vs_test}", exc_info=True)
    
    logger.info("Supagrok Vector Store module self-test finished. Manual cleanup of 'test_rag_storage_v2_final_vs' directory might be needed if errors occurred before cleanup.")
