#!/usr/bin/env python3
# File: /home/owner/supagrok_development_package/supagrok_rag_ingestion_pipeline.py
# Purpose: Supagrok RAG - Ingestion pipeline for documents into PGVector
# PRF-DIRECTIVE: PRF-RAG-PIPELINE-IMPLEMENT-2025-05-08-A
# Based on insights from chat log 681c0c2d... and YouTube video z_LGan-t2Mo
# Author: Supagrok AI Integration Team
# UUID: rag-ingest-f4b1b3e8-0d3c-4a1e-8f2a-7c8d9e0f1a2b

import os
import hashlib
import psycopg2 # type: ignore
from psycopg2.extras import execute_values # type: ignore

# AI Provider specific imports
from openai import OpenAI as OpenAIClient, APIError as OpenAI_APIError, RateLimitError as OpenAI_RateLimitError # type: ignore
import google.generativeai as genai # type: ignore

from dotenv import load_dotenv # type: ignore
from pathlib import Path
from uuid import uuid4
import time
import json
import logging

# === CONFIGURATION ===
load_dotenv()
PG_CONN_STRING = os.getenv("SUPAGROK_PG_CONN_STRING") # e.g., "postgresql://user:pass@host:port/dbname"
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()

# OpenAI specific
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") if AI_PROVIDER == "openai" else None
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")

# Gemini specific
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") if AI_PROVIDER == "gemini" else None
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

DB_EMBEDDING_DIMENSION_STR = os.getenv("DB_EMBEDDING_DIMENSION")
if not DB_EMBEDDING_DIMENSION_STR or not DB_EMBEDDING_DIMENSION_STR.isdigit():
    logging.critical("CRITICAL: DB_EMBEDDING_DIMENSION is not set or not a valid integer in .env file. Exiting.")
    exit(1) # Critical configuration missing
DB_EMBEDDING_DIMENSION = int(DB_EMBEDDING_DIMENSION_STR)


WATCH_DIRECTORY = Path(os.getenv("SUPAGROK_RAG_WATCH_DIR", "./supagrok_data_for_rag/"))

CHUNK_SIZE = int(os.getenv("SUPAGROK_RAG_CHUNK_SIZE", 500)) # Characters
CHUNK_OVERLAP = int(os.getenv("SUPAGROK_RAG_CHUNK_OVERLAP", 50)) # Characters
POLL_INTERVAL_SECONDS = 10

LOG_FILE = Path("/home/owner/supagrok_development_package/rag_ingestion_audit.log")

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# === DATABASE SETUP FUNCTION ===
def setup_database():
    conn = None
    if not PG_CONN_STRING:
        logging.critical("CRITICAL: SUPAGROK_PG_CONN_STRING is not set in .env file. Cannot setup database. Exiting.")
        exit(1)
    try:
        conn = psycopg2.connect(PG_CONN_STRING)
        cur = conn.cursor()
        # Ensure pgvector extension is enabled
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        # Create table for Supagrok RAG documents and chunks
        cur.execute("""
            CREATE TABLE IF NOT EXISTS supagrok_rag_documents (
                id UUID PRIMARY KEY,
                supagrok_source_id VARCHAR(255) NOT NULL, -- e.g., snapshot UUID or log stream name
                source_file_path TEXT NOT NULL,
                file_hash_sha256 VARCHAR(64) NOT NULL,
                document_type VARCHAR(100), -- e.g., 'log', 'config', 'snapshot_metadata'
                metadata JSONB, -- Other Supagrok specific metadata
                ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_source_file_path UNIQUE (source_file_path) -- Ensure unique file paths for stable doc IDs
            );
        """)
        logging.info(f"Creating supagrok_rag_chunks table with embedding VECTOR dimension: {DB_EMBEDDING_DIMENSION}")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS supagrok_rag_chunks (
                id UUID PRIMARY KEY,
                document_id UUID REFERENCES supagrok_rag_documents(id) ON DELETE CASCADE,
                chunk_sequence INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding VECTOR({DB_EMBEDDING_DIMENSION}), -- Configurable dimension
                char_start_offset INTEGER, -- Start character offset in original document
                char_count INTEGER,
                UNIQUE (document_id, chunk_sequence)
            );
        """)
        # Example index, may need tuning based on actual data size and query patterns
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding ON supagrok_rag_chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);")
        conn.commit()
        logging.info(f"Database setup complete. Tables and pgvector extension ensured. Embedding dimension set to {DB_EMBEDDING_DIMENSION}.")
    except psycopg2.Error as e:
        logging.error(f"Database setup failed: {e}")
        if conn:
            conn.rollback()
        # Re-raise to halt execution if DB setup fails, as it's critical
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred during database setup: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()

# === UTILITY FUNCTIONS ===
def get_file_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def chunk_text_recursive(text: str, size: int, overlap: int) -> list[dict]:
    # Returns list of dicts with text and start_offset
    if not text:
        return []
    
    chunk_list = []
    start = 0
    while start < len(text):
        end = start + size
        chunk_list.append({"text": text[start:end], "start_offset": start})
        start += size - overlap
        if start + overlap >= len(text) and end < len(text): 
             if len(text) - start > overlap : 
                chunk_list.append({"text": text[start:], "start_offset": start})
             break
    
    return [c for c in chunk_list if c["text"].strip()]

def get_embeddings(chunks: list[str], ai_provider: str, client: any) -> list[list[float]]:
    embeddings = []
    model_name = ""
    for chunk_idx, chunk_text in enumerate(chunks):
        for attempt in range(3): # Retry mechanism
            try:
                if ai_provider == "openai":
                    model_name = OPENAI_EMBEDDING_MODEL
                    response = client.embeddings.create(input=chunk_text, model=model_name)
                    embedding = response.data[0].embedding
                elif ai_provider == "gemini":
                    model_name = GEMINI_EMBEDDING_MODEL
                    response = genai.embed_content(model=model_name, content=chunk_text)
                    embedding = response['embedding']
                else:
                    raise ValueError(f"Unsupported AI provider for embeddings: {ai_provider}")
                
                # CRITICAL: Validate embedding dimension against configured DB dimension
                if len(embedding) != DB_EMBEDDING_DIMENSION:
                    error_msg = (f"CRITICAL DIMENSION MISMATCH: {ai_provider.upper()} model '{model_name}' "
                                 f"produced embedding of dimension {len(embedding)}, but DB_EMBEDDING_DIMENSION "
                                 f"is configured to {DB_EMBEDDING_DIMENSION}. This will cause DB errors or incorrect results. "
                                 f"Please align your AI model choice and .env configuration for DB_EMBEDDING_DIMENSION, "
                                 f"then re-run database setup if DB_EMBEDDING_DIMENSION was changed.")
                    logging.critical(error_msg)
                    # Halt processing for this document to prevent inserting bad data.
                    # Depending on desired strictness, could halt entire pipeline.
                    raise ValueError(error_msg) 

                embeddings.append(embedding)
                logging.debug(f"Embedding generated for chunk {chunk_idx + 1}/{len(chunks)}")
                break 
            except (OpenAI_RateLimitError, Exception) as e: 
                logging.warning(f"Rate limit or API issue for chunk {chunk_idx} with {ai_provider.upper()} (model: {model_name}), attempt {attempt+1}. Retrying after {2**attempt}s: {e}")
                time.sleep(2**attempt + 0.1) 
            except (OpenAI_APIError, Exception) as e: 
                logging.error(f"{ai_provider.upper()} API error for chunk {chunk_idx} (model: {model_name}), attempt {attempt+1}: {e}")
                time.sleep(2**attempt)
            if attempt == 2:
                logging.error(f"Failed to embed chunk {chunk_idx} (model: {model_name}) after multiple retries.")
                # Re-raise to signal failure for this chunk/document
                raise Exception(f"Failed to embed chunk {chunk_idx} after multiple retries.")
    return embeddings

def store_document_and_chunks(conn, doc_id_for_insert_attempt: uuid4, supagrok_source_id: str, file_path: Path, file_hash: str, doc_type: str, chunk_objects: list[dict], embeddings: list[list[float]]):
    cur = conn.cursor()
    try:
        resolved_file_path_str = str(file_path.resolve())
        cur.execute("""
            INSERT INTO supagrok_rag_documents (id, supagrok_source_id, source_file_path, file_hash_sha256, document_type, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_file_path) DO UPDATE 
            SET 
                file_hash_sha256 = EXCLUDED.file_hash_sha256,
                updated_at = CURRENT_TIMESTAMP,
                supagrok_source_id = EXCLUDED.supagrok_source_id, 
                document_type = EXCLUDED.document_type,
                metadata = EXCLUDED.metadata
            RETURNING id; 
        """, (str(doc_id_for_insert_attempt), supagrok_source_id, resolved_file_path_str, file_hash, doc_type, json.dumps({"original_filename": file_path.name})))
        
        returned_id_tuple = cur.fetchone()
        if not returned_id_tuple:
            raise Exception(f"Failed to insert or update document for {file_path.name}")
        actual_doc_id = returned_id_tuple[0] 

        cur.execute("DELETE FROM supagrok_rag_chunks WHERE document_id = %s;", (str(actual_doc_id),))

        chunk_data_tuples = []
        for i, (chunk_obj, embedding_vector) in enumerate(zip(chunk_objects, embeddings)):
            chunk_data_tuples.append((
                str(uuid4()), str(actual_doc_id), i + 1, chunk_obj["text"], embedding_vector, chunk_obj["start_offset"], len(chunk_obj["text"])
            ))
        
        execute_values(cur, """
            INSERT INTO supagrok_rag_chunks (id, document_id, chunk_sequence, chunk_text, embedding, char_start_offset, char_count)
            VALUES %s;
        """, chunk_data_tuples)
        
        conn.commit()
        logging.info(f"Stored document {actual_doc_id} ({file_path.name}) with {len(chunk_objects)} chunks.")
    except Exception as e:
        conn.rollback()
        logging.error(f"Error storing document/chunks for {file_path.name}: {e}")
        raise
    finally:
        cur.close()

# === MAIN PROCESSING LOOP ===
def watch_and_process_supagrok_data():
    if not PG_CONN_STRING:
        logging.critical("CRITICAL: SUPAGROK_PG_CONN_STRING is not set in .env file. Exiting.")
        exit(1)

    ai_client: any = None
    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY: logging.critical("AI_PROVIDER is openai, but OPENAI_API_KEY is missing. Exiting."); exit(1)
        ai_client = OpenAIClient(api_key=OPENAI_API_KEY)
    elif AI_PROVIDER == "gemini":
        if not GOOGLE_API_KEY: logging.critical("AI_PROVIDER is gemini, but GOOGLE_API_KEY is missing. Exiting."); exit(1)
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            # Test configuration by trying to list models, for example
            # models = [m for m in genai.list_models() if 'embedContent' in m.supported_generation_methods]
            # if not models:
            #     logging.critical("Gemini configured, but no suitable embedding models found or API key invalid. Exiting.")
            #     exit(1)
            ai_client = genai 
        except Exception as e:
            logging.critical(f"Failed to configure Gemini AI: {e}. Exiting.")
            exit(1)
    else:
        logging.critical(f"Unsupported AI_PROVIDER: {AI_PROVIDER}. Exiting.")
        exit(1)

    WATCH_DIRECTORY.mkdir(parents=True, exist_ok=True)
    logging.info(f"Watching directory: {WATCH_DIRECTORY.resolve()} for Supagrok RAG data.")
    logging.info(f"Using AI Provider: {AI_PROVIDER.upper()}, DB Embedding Dimension: {DB_EMBEDDING_DIMENSION}")
    
    processed_files_hashes = {} 

    conn = psycopg2.connect(PG_CONN_STRING)

    while True:
        try:
            for filepath in WATCH_DIRECTORY.glob("**/*"): 
                if filepath.is_file() and filepath.suffix in ['.txt', '.log', '.md', '.json', '.yaml', '.conf']: 
                    resolved_path_str = str(filepath.resolve())
                    current_file_hash = get_file_sha256(filepath)
                    
                    if resolved_path_str not in processed_files_hashes or processed_files_hashes[resolved_path_str] != current_file_hash:
                        logging.info(f"Processing file: {filepath.name} (Hash: {current_file_hash[:8]})")
                        
                        try:
                            with open(filepath, "r", encoding="utf-8") as f:
                                text_content = f.read()
                        except Exception as e:
                            logging.error(f"Could not read file {filepath}: {e}")
                            continue
                        
                        supagrok_source_id = filepath.parent.name if filepath.parent != WATCH_DIRECTORY else "general_docs"
                        doc_type = filepath.suffix.lstrip('.')
                        
                        temp_doc_id_for_insert = uuid4() 

                        chunk_objects = chunk_text_recursive(text_content, CHUNK_SIZE, CHUNK_OVERLAP)
                        if not chunk_objects:
                            logging.warning(f"No text chunks generated for {filepath.name}. Skipping.")
                            processed_files_hashes[resolved_path_str] = current_file_hash 
                            continue

                        try:
                            text_chunks_for_embedding = [c["text"] for c in chunk_objects]
                            chunk_embeddings = get_embeddings(text_chunks_for_embedding, AI_PROVIDER, ai_client)
                        except ValueError as ve: # Catch dimension mismatch from get_embeddings
                            logging.error(f"Halting processing for file {filepath.name} due to critical error: {ve}")
                            # Optionally, mark this file as "error" in processed_files_hashes to avoid retrying until config is fixed
                            # processed_files_hashes[resolved_path_str] = "ERROR_" + current_file_hash 
                            continue # Skip to next file
                        except Exception as emb_ex: # Catch other embedding errors
                            logging.error(f"Failed to generate embeddings for {filepath.name}: {emb_ex}. Skipping file.")
                            continue


                        if len(chunk_objects) != len(chunk_embeddings):
                            logging.error(f"Mismatch between chunk object count ({len(chunk_objects)}) and embedding count ({len(chunk_embeddings)}) for {filepath.name}. Skipping.")
                            continue

                        store_document_and_chunks(conn, temp_doc_id_for_insert, supagrok_source_id, filepath, current_file_hash, doc_type, chunk_objects, chunk_embeddings)
                        processed_files_hashes[resolved_path_str] = current_file_hash
                        logging.info(f"Successfully processed and stored: {filepath.name}")

        except psycopg2.OperationalError as db_op_error:
            logging.error(f"Database operational error: {db_op_error}. Reconnecting...")
            if conn: conn.close()
            time.sleep(5) 
            try:
                conn = psycopg2.connect(PG_CONN_STRING)
                logging.info("Reconnected to database.")
            except Exception as reconn_e:
                logging.error(f"Failed to reconnect to database: {reconn_e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL_SECONDS)

    if conn: conn.close() 

if __name__ == "__main__":
    try:
        setup_database()
        watch_and_process_supagrok_data()
    except Exception as e:
        logging.critical(f"Supagrok RAG Ingestion Pipeline failed to start or encountered a critical error: {e}", exc_info=True)
        # Exit with a non-zero code to indicate failure, useful for service managers
        exit(1)
