#!/usr/bin/env python3
# PRF-SUPAGROK-RAGDOCLOADER-2025-05-10
# UUID: docload-c3d4e5f6-a7b8-9012-3456-7890abcdef
# Timestamp: 2025-05-10T19:30:00Z
# Last Modified: 2025-05-10T20:00:00Z 
# Description: (supagrok_rag_system_v2_final/supagrok_rag_document_loader.py) Loads and parses documents from files, directories, or YouTube URLs for the RAG system.
# Dependencies: Python packages: llama_index.core. System dependencies: None directly. Uses supagrok_youtube_ingest_utils.
# Inputs: Path to a document, a directory of documents, or a YouTube video URL.
# Outputs: List of LlamaIndex Document objects.
# Version: 1.3.1
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

from pathlib import Path
import logging
import re
from llama_index.core import SimpleDirectoryReader, Document
from typing import List, Union

import supagrok_youtube_ingest_utils 
import supagrok_rag_config 

logger = logging.getLogger(__name__)

YOUTUBE_URL_PATTERN_DOCLOAD = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/(watch\?v=|embed/|shorts/|live/)|youtu\.be/)([a-zA-Z0-9_-]{11}).*$"
)

def _is_youtube_url(url_string: str) -> bool:
    """Checks if the given string is a YouTube video URL."""
    return YOUTUBE_URL_PATTERN_DOCLOAD.match(url_string) is not None

def _load_document_from_youtube(video_url: str) -> List[Document]:
    """
    Fetches subtitles from a YouTube URL and converts them into LlamaIndex Documents.
    """
    logger.info(f"Attempting to load document from YouTube URL: {video_url}")
    preferred_langs = supagrok_rag_config.get_youtube_preferred_subtitle_langs()
    subtitle_data = supagrok_youtube_ingest_utils.fetch_youtube_subtitle_text(video_url, preferred_langs)

    if subtitle_data and subtitle_data["text"] and subtitle_data["text"].strip():
        doc_text = subtitle_data["text"]
        metadata = {
            "source_type": "youtube_video_subtitles", 
            "video_title": subtitle_data.get("title", "Unknown YouTube Title"),
            "video_url": subtitle_data.get("url", video_url),
            "subtitle_language_code": subtitle_data.get("language", "unknown"),
            "original_input_source": video_url, 
            "content_length_chars": len(doc_text)
        }
        doc = Document(text=doc_text, metadata=metadata, doc_id=f"youtube_{video_url}")
        logger.info(f"Successfully created LlamaIndex Document from YouTube URL: {video_url} (Title: {metadata['video_title']})")
        return [doc]
    else:
        logger.warning(f"Could not retrieve or parse valid/non-empty subtitles for YouTube URL: {video_url}")
        return []


def load_documents(input_source_str: str) -> List[Document]:
    """
    Loads documents from the given file path, directory path, or YouTube URL.
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

    logger.info(f"Loading documents from local file/directory: {input_path}")
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
        logger.error(f"Failed to load documents from local file/directory {input_path}: {e}", exc_info=True)
        raise 

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) 
    
    test_data_main_dir = Path.cwd() / "test_doc_loader_main_data"
    test_data_main_dir.mkdir(exist_ok=True)
    test_file_main_path = test_data_main_dir / "sample_main_test_file.txt"
    with open(test_file_main_path, "w", encoding="utf-8") as f:
        f.write("This is a test document from a local file for the document loader's main test.")
    
    logger.info(f"--- Testing document loader with single file: {test_file_main_path} ---")
    try:
        docs_from_file = load_documents(str(test_file_main_path))
        for doc_index, doc_object in enumerate(docs_from_file): 
            logger.info(f"File Doc {doc_index+1} ID: {doc_object.doc_id}, Text Preview: {doc_object.text[:70].strip()}...")
            logger.info(f"Metadata: {doc_object.metadata}")
    except Exception as e_file_test: 
        logger.error(f"Error testing single file loading: {e_file_test}", exc_info=True)

    test_youtube_url_main = "https://www.youtube.com/watch?v=z_LGan-t2Mo" 
    logger.info(f"--- Testing document loader with YouTube URL: {test_youtube_url_main} ---")
    if supagrok_youtube_ingest_utils.check_yt_dlp_availability():
        try:
            docs_from_youtube = load_documents(test_youtube_url_main)
            if docs_from_youtube:
                for doc_index, doc_object in enumerate(docs_from_youtube): 
                    logger.info(f"YouTube Doc {doc_index+1} ID: {doc_object.doc_id}, Title: {doc_object.metadata.get('video_title')}")
                    logger.info(f"Text Preview (first 100 chars): {doc_object.text[:100].strip()}...")
                    logger.info(f"Metadata: {doc_object.metadata}")
            else:
                logger.warning(f"No documents were returned from YouTube URL: {test_youtube_url_main}")
        except Exception as e_yt_test: 
            logger.error(f"Error testing YouTube URL loading: {e_yt_test}", exc_info=True)
    else:
        logger.warning("yt-dlp is not available, skipping YouTube URL load test in document_loader's main block.")

    logger.info("Supagrok Document Loader self-test finished. Manual cleanup of 'test_doc_loader_main_data' directory might be needed.")
