#!/usr/bin/env python3
# PRF-SUPAGROK-RAGCLI-2025-05-10
# UUID: cli-f6a7b8c9-d0e1-2345-6789-0abcdef012
# Timestamp: 2025-05-10T19:30:00Z
# Last Modified: 2025-05-10T20:00:00Z 
# Description: (supagrok_rag_system_v2_final/supagrok_rag_cli.py) Command Line Interface for the Supagrok RAG system. Handles ingestion from files, directories, or YouTube URLs, and querying.
# Dependencies: Python packages: argparse. Uses local supagrok_rag_* modules.
# Inputs: Command-line arguments for ingestion or querying.
# Outputs: Console output (status messages, query responses, errors).
# Version: 1.3.1
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import argparse
import logging
import sys 
from pathlib import Path 

try:
    import supagrok_rag_config as app_config 
    import supagrok_rag_vector_store as app_vector_store 
    import supagrok_rag_document_loader as app_doc_loader
    import supagrok_rag_query_engine as app_query_engine
except ValueError as ve_cli_config: 
    print(f"CRITICAL CLI Error: Failed to initialize core RAG components, likely due to configuration (e.g., OpenAI API Key): {ve_cli_config}", file=sys.stderr)
    print("Please ensure your OPENAI_API_KEY is correctly set in a .env file (e.g., .env_rag if using the setup script) and is accessible.", file=sys.stderr)
    sys.exit(1)
except ImportError as e_cli_import:
    print(f"CRITICAL CLI Error: Could not import one or more Supagrok RAG modules: {e_cli_import}", file=sys.stderr)
    print(f"Please ensure you are running this CLI script from its project directory (expected: {Path.cwd()})", file=sys.stderr)
    print("and that all 'supagrok_rag_*.py' files are present in the same directory.", file=sys.stderr)
    sys.exit(1)
except Exception as e_cli_critical_setup: 
    print(f"CRITICAL CLI Error during initial module loading phase: {e_cli_critical_setup}", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SupagrokRAG_CLI_App") 

def handle_ingest_command(args: argparse.Namespace) -> None:
    """Handles the 'ingest' command logic."""
    logger.info(f"Starting ingestion process for input source: '{args.input_source}'")
    try:
        app_config.ensure_openai_api_key() 
        
        logger.info("Loading documents from source...")
        documents_to_ingest = app_doc_loader.load_documents(args.input_source)
        if not documents_to_ingest:
            logger.warning("No documents were loaded from the specified source. Ingestion cannot proceed.")
            print("Warning: No documents found or loaded. Please check the input source (file, directory, or YouTube URL) and its content/availability.")
            return 

        logger.info(f"Successfully loaded {len(documents_to_ingest)} document(s). Proceeding with indexing into vector store.")
        app_vector_store.create_and_persist_index(documents_to_ingest) 
        
        logger.info("Ingestion process completed successfully.")
        print(f"\n✅ Ingestion complete. Index created/updated in storage directory: {app_config.get_storage_path()}")

    except FileNotFoundError as e_cli_fnf:
        logger.error(f"Ingestion failed: Input source not found: {e_cli_fnf}")
        print(f"Error: Input source '{args.input_source}' not found. Please check the path or URL.")
    except ValueError as e_cli_val: 
        logger.error(f"Ingestion failed due to a value or configuration error: {e_cli_val}")
        print(f"Error: {e_cli_val}")
    except Exception as e_cli_unexpected_ingest: 
        logger.error(f"An unexpected error occurred during the ingestion process: {e_cli_unexpected_ingest}", exc_info=True)
        print(f"An unexpected error occurred during ingestion. Please check the logs for more details: {e_cli_unexpected_ingest}")

def handle_query_command(args: argparse.Namespace) -> None:
    """Handles the 'query' command logic."""
    logger.info(f"Received query for RAG system: '{args.query_text}'")
    try:
        app_config.ensure_openai_api_key() 

        query_engine_instance = app_query_engine.get_query_engine() 
        if not query_engine_instance:
            print("Error: Could not initialize the RAG query engine. Please ensure data has been ingested successfully and the API key is configured correctly.")
            return

        answer_from_rag = app_query_engine.execute_query(args.query_text, query_engine_instance)
        
        logger.info("Query processed by RAG system.")
        print("\n🤖 Supagrok RAG System Answer:")
        print("=" * 40)
        print(answer_from_rag if answer_from_rag is not None else "No answer could be generated, or an error occurred during processing.")
        print("=" * 40)

    except ValueError as e_cli_val_query: 
        logger.error(f"Query failed due to a value or configuration error: {e_cli_val_query}")
        print(f"Error: {e_cli_val_query}")
    except Exception as e_cli_unexpected_query: 
        logger.error(f"An unexpected error occurred during the query process: {e_cli_unexpected_query}", exc_info=True)
        print(f"An unexpected error occurred during query. Please check the logs for more details: {e_cli_unexpected_query}")

def main_application_cli() -> None: 
    """Main function to parse command-line arguments and dispatch to appropriate handlers."""
    parser = argparse.ArgumentParser(
        description="Supagrok RAG System Command Line Interface. \n"
                    "This tool allows ingestion of documents from various sources (local files, directories, YouTube video subtitles) \n"
                    "into a LlamaIndex vector store, and enables querying this knowledge base using a RAG approach.",
        formatter_class=argparse.RawTextHelpFormatter 
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands: 'ingest' or 'query'", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents into the RAG system's vector store.")
    ingest_parser.add_argument(
        "input_source", 
        type=str, 
        help="The source for document ingestion. This can be: \n"
             "  - A path to a single document file (e.g., /path/to/your_document.txt)\n"
             "  - A path to a directory containing multiple documents (e.g., /path/to/your_docs_folder/)\n"
             "  - A full YouTube video URL (e.g., 'https://www.youtube.com/watch?v=VIDEO_ID')"
    )
    ingest_parser.set_defaults(func=handle_ingest_command)

    query_parser = subparsers.add_parser("query", help="Query the RAG system using the knowledge from ingested documents.")
    query_parser.add_argument("query_text", type=str, help="The question or query text to ask the RAG system.")
    query_parser.set_defaults(func=handle_query_command)

    if len(sys.argv) == 1: 
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    parsed_args = parser.parse_args()
    
    logger.info(f"Supagrok RAG CLI: Executing command '{parsed_args.command}'...")
    if hasattr(parsed_args, 'func'):
        parsed_args.func(parsed_args) 
    else: 
        logger.error("No function associated with the parsed command. This indicates an internal CLI error.")
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    logger.info(f"Command '{parsed_args.command}' finished processing.")

if __name__ == "__main__":
    main_application_cli()
