#!/usr/bin/env python3
# PRF-SUPAGROK-RAGVECTORSTORE-2025-05-10
# UUID: 3d4e6f8a-0b2c-44d5-e6f7-a8b9c0d1e2f3
# Timestamp: 2025-05-10T16:15:00Z
# Last Modified: 2025-05-10T18:10:00Z # Ensuring latest version for re-emission
# Description: (supagrok_rag_system_v2/supagrok_rag_vector_store.py) Manages the LlamaIndex vector store for the RAG system.
# Dependencies: Python packages: llama_index.core, llama_index.llms.openai, llama_index.embeddings.huggingface. Uses supagrok_rag_config.
# Inputs: List of LlamaIndex Document objects for ingestion, storage path.
# Outputs: Creates/updates a vector index on disk. Loads an index from disk.
# Version: 1.1.1
# Author: SupagrokAgent/1.4
# PRF-Codex-Version: 1.6

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
    logger.info(f"LlamaIndex global LLM set to: {Settings.llm.metadata.model_name}")
    logger.info(f"LlamaIndex global Embedding model set to: {Settings.embed_model.model_name}")
except ValueError as e:
    logger.critical(f"CRITICAL FAILURE in LlamaIndex Settings: OpenAI API key issue: {e}")
    logger.critical("The RAG system (indexing/querying) will NOT function without a valid API key for the LLM.")
    raise 
except Exception as e:
    logger.critical(f"CRITICAL FAILURE: Unexpected error configuring LlamaIndex Settings: {e}", exc_info=True)
    raise


def create_and_persist_index(documents: List[Document], persist_dir_override: TypingOptional[Path] = None) -> VectorStoreIndex:
    """Creates a new vector index from documents and persists it to disk."""
    if not documents:
        logger.error("No documents provided for indexing. Aborting index creation.")
        raise ValueError("Cannot create an index from an empty list of documents.")

    persist_dir_actual = persist_dir_override if persist_dir_override else supagrok_rag_config.get_storage_path()
    persist_dir_actual.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Creating/updating index in: {persist_dir_actual} with {len(documents)} document(s).")
    logger.info(f"Using LLM: {Settings.llm.metadata.model_name} and Embed Model: {Settings.embed_model.model_name}")

    try:
        index = VectorStoreIndex.from_documents(
            documents,
            show_progress=True, 
        )
        index.storage_context.persist(persist_dir=str(persist_dir_actual))
        logger.info(f"Successfully created/updated and persisted index at {persist_dir_actual}.")
        return index
    except Exception as e:
        logger.error(f"Failed to create or persist index at {persist_dir_actual}: {e}", exc_info=True)
        raise

def load_persisted_index(persist_dir_override: TypingOptional[Path] = None) -> TypingOptional[VectorStoreIndex]:
    """Loads an existing vector index. Returns None if not found or load fails."""
    persist_dir_actual = persist_dir_override if persist_dir_override else supagrok_rag_config.get_storage_path()

    if not persist_dir_actual.exists() or not any(persist_dir_actual.iterdir()):
        logger.warning(f"Index persistence directory {persist_dir_actual} does not exist or is empty. Cannot load index.")
        return None

    logger.info(f"Attempting to load index from: {persist_dir_actual}")
    logger.info(f"Using LLM: {Settings.llm.metadata.model_name} and Embed Model: {Settings.embed_model.model_name} for loading.")
    try:
        storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir_actual))
        index = load_index_from_storage(storage_context)
        logger.info(f"Successfully loaded index from {persist_dir_actual}.")
        return index
    except FileNotFoundError: 
        logger.error(f"Core index files not found in {persist_dir_actual}. Has an index been created here?")
        return None
    except Exception as e:
        logger.error(f"Failed to load index from {persist_dir_actual}: {e}", exc_info=True)
        logger.error("The storage might be corrupted, incomplete, or incompatible. Consider re-ingesting.")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Vector Store module self-test initiated.")
    
    try:
        logger.info("Global LlamaIndex Settings should be configured by now.")
        
        doc1 = Document(text="The quick brown fox jumps over the lazy dog.")
        doc2 = Document(text="Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
        test_documents = [doc1, doc2]

        test_storage_dir = Path.cwd() / "test_rag_storage_v2_vs"
        if test_storage_dir.exists(): 
            import shutil
            shutil.rmtree(test_storage_dir)
            logger.info(f"Cleaned up existing test storage directory: {test_storage_dir}")

        logger.info("--- Testing index creation and persistence ---")
        created_index = create_and_persist_index(test_documents, persist_dir_override=test_storage_dir)
        if created_index: 
            logger.info(f"Index created. Number of docs in store: {len(created_index.docstore.docs)}")

        logger.info("--- Testing index loading ---")
        loaded_index = load_persisted_index(persist_dir_override=test_storage_dir)
        if loaded_index:
            logger.info(f"Index loaded. Number of docs in store: {len(loaded_index.docstore.docs)}")
            query_engine_test = loaded_index.as_query_engine()
            response = query_engine_test.query("What does the fox jump over?")
            logger.info(f"Test query response: {response}")
        else:
            logger.warning("Could not load index for self-testing.")
            
    except ValueError as ve: 
        logger.error(f"Vector Store Self-Test FAILED due to configuration error (likely API key for LlamaIndex Settings): {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during vector store self-test: {e}", exc_info=True)
    
    logger.info("Vector Store module self-test finished. Manual cleanup of 'test_rag_storage_v2_vs' might be needed if errors occurred.")
