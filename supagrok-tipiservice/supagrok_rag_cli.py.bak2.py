#!/usr/bin/env python3
# PRF-SUPAGROK-RAGCLI-2025-05-10
# UUID: 5f6a8b0c-2d4e-66f7-g8a9-b0c1d2e3f4g5
# Timestamp: 2025-05-10T16:25:00Z
# Last Modified: 2025-05-10T18:10:00Z # Ensuring latest version for re-emission
# Description: (supagrok_rag_system_v2/supagrok_rag_cli.py) Command Line Interface for the Supagrok RAG system. Handles ingestion from files, directories, or YouTube URLs, and querying.
# Dependencies: Python packages: argparse. Uses local supagrok_rag_* modules.
# Inputs: Command-line arguments for ingestion or querying.
# Outputs: Console output (status messages, query responses, errors).
# Version: 1.2.1
# Author: SupagrokAgent/1.4
# PRF-Codex-Version: 1.6

import argparse
import logging
import sys 

try:
    import supagrok_rag_config as config
    import supagrok_rag_vector_store as vector_store 
    import supagrok_rag_document_loader as doc_loader
    import supagrok_rag_query_engine as query_engine
except ValueError as ve_config: 
    print(f"CRITICAL CLI Error: Failed to initialize core components, likely due to configuration (e.g., OpenAI API Key): {ve_config}", file=sys.stderr)
    print("Please ensure your OPENAI_API_KEY is correctly set in a .env file and accessible.", file=sys.stderr)
    sys.exit(1)
except ImportError as e_import:
    print(f"CRITICAL CLI Error: Could not import Supagrok RAG modules: {e_import}", file=sys.stderr)
    print("Ensure you are running the CLI from the project's root directory (e.g. /opt/supagrok/supagrok_rag_system_v2/)", file=sys.stderr)
    print("or that the modules are correctly placed in your PYTHONPATH.", file=sys.stderr)
    sys.exit(1)
except Exception as e_critical_setup: 
    print(f"CRITICAL CLI Error during initial module loading: {e_critical_setup}", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SupagrokRAG_CLI") 

def handle_ingest(args: argparse.Namespace) -> None:
    """Handles the 'ingest' command."""
    logger.info(f"Starting ingestion for input source: '{args.input_source}'")
    try:
        config.ensure_openai_api_key() 
        
        logger.info("Loading documents...")
        documents = doc_loader.load_documents(args.input_source)
        if not documents:
            logger.warning("No documents were loaded from the source. Ingestion cannot proceed.")
            print("Warning: No documents found or loaded. Please check the input source and its content/availability.")
            return 

        logger.info(f"Successfully loaded {len(documents)} document(s). Proceeding with indexing.")
        vector_store.create_and_persist_index(documents) 
        
        logger.info("Ingestion process completed successfully.")
        print(f"\n✅ Ingestion complete. Index created/updated in: {config.get_storage_path()}")

    except FileNotFoundError as e_fnf:
        logger.error(f"Ingestion failed: Input source not found: {e_fnf}")
        print(f"Error: Input source not found. Please check the path or URL: {args.input_source}")
    except ValueError as e_val: 
        logger.error(f"Ingestion failed due to a value or configuration error: {e_val}")
        print(f"Error: {e_val}")
    except Exception as e_unexpected:
        logger.error(f"An unexpected error occurred during ingestion: {e_unexpected}", exc_info=True)
        print(f"An unexpected error occurred during ingestion. Check logs for details: {e_unexpected}")

def handle_query(args: argparse.Namespace) -> None:
    """Handles the 'query' command."""
    logger.info(f"Received query: '{args.query_text}'")
    try:
        config.ensure_openai_api_key() 

        q_engine_instance = query_engine.get_query_engine() 
        if not q_engine_instance:
            print("Error: Could not initialize query engine. Has data been ingested and API key configured correctly?")
            return

        answer = query_engine.execute_query(args.query_text, q_engine_instance)
        
        logger.info("Query processed.")
        print("\n🤖 Supagrok RAG Answer:")
        print("=" * 30)
        print(answer if answer is not None else "No answer could be generated, or an error occurred.")
        print("=" * 30)

    except ValueError as e_val: 
        logger.error(f"Query failed due to a value or configuration error: {e_val}")
        print(f"Error: {e_val}")
    except Exception as e_unexpected:
        logger.error(f"An unexpected error occurred during query: {e_unexpected}", exc_info=True)
        print(f"An unexpected error occurred during query. Check logs for details: {e_unexpected}")

def main() -> None:
    """Main function to parse arguments and dispatch commands."""
    parser = argparse.ArgumentParser(
        description="Supagrok RAG System CLI. Ingests documents from files, directories, or YouTube URLs, and allows querying.",
        formatter_class=argparse.RawTextHelpFormatter 
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands (ingest, query)", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents into the vector store.")
    ingest_parser.add_argument(
        "input_source", 
        type=str, 
        help="Source for ingestion: \n"
             "  - Path to a document file (e.g., /path/to/doc.txt)\n"
             "  - Path to a directory of documents (e.g., /path/to/docs/)\n"
             "  - A YouTube video URL (e.g., 'https://www.youtube.com/watch?v=VIDEO_ID')"
    )
    ingest_parser.set_defaults(func=handle_ingest)

    query_parser = subparsers.add_parser("query", help="Query the ingested documents using the RAG system.")
    query_parser.add_argument("query_text", type=str, help="The question or query text to ask the RAG system.")
    query_parser.set_defaults(func=handle_query)

    if len(sys.argv) == 1: 
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    
    logger.info(f"Supagrok RAG CLI: Executing command '{args.command}'...")
    if hasattr(args, 'func'):
        args.func(args)
    else: 
        logger.error("No function associated with the parsed command.")
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    logger.info(f"Command '{args.command}' finished processing.")

if __name__ == "__main__":
    main()
