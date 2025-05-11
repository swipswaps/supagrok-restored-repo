#!/usr/bin/env python3
# PRF-SUPAGROK-RAGDOCLOADER-2025-05-10
# UUID: 2c3d5e7f-9a1b-33c4-d5e6-f7a8b9c0d1e2
# Timestamp: 2025-05-10T16:10:00Z
# Last Modified: 2025-05-10T18:10:00Z # Ensuring latest version for re-emission
# Description: (supagrok_rag_system_v2/supagrok_rag_document_loader.py) Loads and parses documents from files, directories, or YouTube URLs for the RAG system.
# Dependencies: Python packages: llama_index.core. System dependencies: None directly. Uses supagrok_youtube_ingest_utils.
# Inputs: Path to a document, a directory of documents, or a YouTube video URL.
# Outputs: List of LlamaIndex Document objects.
# Version: 1.2.1
# Author: SupagrokAgent/1.4
# PRF-Codex-Version: 1.6

from pathlib import Path
import logging
import re
from llama_index.core import SimpleDirectoryReader, Document
from typing import List, Union

import supagrok_youtube_ingest_utils
import supagrok_rag_config

logger = logging.getLogger(__name__)

YOUTUBE_URL_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/(watch\?v=|embed/|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11}).*$"
)

def _is_youtube_url(url_string: str) -> bool:
    """Checks if the given string is a YouTube video URL."""
    return YOUTUBE_URL_PATTERN.match(url_string) is not None

def _load_document_from_youtube(video_url: str) -> List[Document]:
    """Fetches YouTube subtitles and converts to LlamaIndex Documents."""
    logger.info(f"Attempting to load document from YouTube URL: {video_url}")
    preferred_langs = supagrok_rag_config.get_youtube_preferred_subtitle_langs()
    subtitle_data = supagrok_youtube_ingest_utils.fetch_youtube_subtitle_text(video_url, preferred_langs)

    if subtitle_data and subtitle_data["text"] and subtitle_data["text"].strip():
        doc_text = subtitle_data["text"]
        metadata = {
            "source_type": "youtube",
            "video_title": subtitle_data.get("title", "Unknown YouTube Title"),
            "video_url": subtitle_data.get("url", video_url),
            "language": subtitle_data.get("language", "unknown"),
            "original_filename": video_url, 
            "content_length_chars": len(doc_text)
        }
        doc = Document(text=doc_text, metadata=metadata, doc_id=video_url)
        logger.info(f"Successfully created LlamaIndex Document from YouTube URL: {video_url} (Title: {metadata['video_title']})")
        return [doc]
    else:
        logger.warning(f"Could not retrieve or parse valid/non-empty subtitles for YouTube URL: {video_url}")
        return []


def load_documents(input_source_str: str) -> List[Document]:
    """
    Loads documents from a file path, directory path, or YouTube URL.
    """
    if not input_source_str or not input_source_str.strip():
        logger.error("Input source string is empty or None.")
        raise ValueError("Input source cannot be empty.")

    if _is_youtube_url(input_source_str):
        return _load_document_from_youtube(input_source_str)

    input_path = Path(input_source_str)
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    logger.info(f"Loading documents from file/directory: {input_path}")
    try:
        if input_path.is_file():
            documents = SimpleDirectoryReader(
                input_dir=str(input_path.parent),
                input_files=[input_path.name] 
            ).load_data()
            logger.info(f"Loaded 1 document: {input_path.name}")
        elif input_path.is_dir():
            reader = SimpleDirectoryReader(
                input_dir=str(input_path),
                recursive=True, 
            )
            documents = reader.load_data()
            logger.info(f"Loaded {len(documents)} documents from directory: {input_path}")
        else: 
            msg = f"Input path is not a recognized type (file, directory, or YouTube URL): {input_path}"
            logger.error(msg)
            raise ValueError(msg)
        
        if not documents:
            logger.warning(f"No documents were loaded from {input_path}. Check file types, content, or permissions.")
        
        return documents
    except Exception as e:
        logger.error(f"Failed to load documents from file/directory {input_path}: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_dir_files_v2 = Path.cwd() / "test_doc_loader_data_v2"
    test_dir_files_v2.mkdir(exist_ok=True)
    test_file_path_v2 = test_dir_files_v2 / "sample_file_v2.txt"
    with open(test_file_path_v2, "w", encoding="utf-8") as f:
        f.write("This is a test document from a local file for version 2.")
    
    logger.info(f"--- Testing with single file: {test_file_path_v2} ---")
    try:
        docs_file = load_documents(str(test_file_path_v2))
        for doc_idx, doc_item in enumerate(docs_file): 
            logger.info(f"File Doc {doc_idx+1} ID: {doc_item.doc_id}, Text: {doc_item.text[:60].strip()}...")
            logger.info(f"Metadata: {doc_item.metadata}")
    except Exception as e: 
        logger.error(f"Error testing single file: {e}", exc_info=True)

    test_yt_url_v2 = "https://www.youtube.com/watch?v=z_LGan-t2Mo" 
    logger.info(f"--- Testing with YouTube URL: {test_yt_url_v2} ---")
    if supagrok_youtube_ingest_utils.check_yt_dlp_availability():
        try:
            docs_yt = load_documents(test_yt_url_v2)
            if docs_yt:
                for doc_idx, doc_item in enumerate(docs_yt): 
                    logger.info(f"YT Doc {doc_idx+1} ID: {doc_item.doc_id}, Title: {doc_item.metadata.get('video_title')}")
                    logger.info(f"Text (first 100 chars): {doc_item.text[:100].strip()}...")
                    logger.info(f"Metadata: {doc_item.metadata}")
            else:
                logger.warning(f"No documents returned for YouTube URL: {test_yt_url_v2}")
        except Exception as e: 
            logger.error(f"Error testing YouTube URL: {e}", exc_info=True)
    else:
        logger.warning("yt-dlp not available, skipping YouTube URL load test in document_loader.")

    logger.info("Document loader self-test finished. Manual cleanup of 'test_doc_loader_data_v2' directory might be needed.")
