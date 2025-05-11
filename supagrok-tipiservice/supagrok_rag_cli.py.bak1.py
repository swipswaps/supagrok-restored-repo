#!/usr/bin/env python3
# PRF-SUPAGROK-RAGCLI-2025-05-09
# UUID: e5f6a7b8-c9d0-1234-5678-90abcdef0123
# Timestamp: 2025-05-09T14:20:00Z
# Last Modified: 2025-05-09T14:20:00Z
# Description: /opt/supagrok/supagrok_rag_system/supagrok_rag_cli.py - Command Line Interface for the Supagrok RAG system.
# Dependencies: argparse, logging, supagrok_rag_config, supagrok_rag_document_loader, supagrok_rag_vector_store, supagrok_rag_query_engine
# Inputs: Command-line arguments for ingestion or querying.
# Outputs: Console output (status messages, query responses, errors).
# Version: 1.0.0
# Author: SupagrokAgent/1.2
# PRF-Codex-Version: 1.4

import argparse
import logging
import sys # For sys.exit

# Assuming these modules are in the same directory or Python path
try:
    import supagrok_rag_config as config
    import supagrok_rag_document_loader as doc_loader
    import supagrok_rag_vector_store as vector_store
    import supagrok_rag_query_engine as query_engine
except ImportError as e:
    # This can happen if the script is not run from the correct directory
    # or if PYTHONPATH is not set up.
    print(f"Error: Could not import Supagrok RAG modules: {e}", file=sys.stderr)
    print("Please ensure you are running the CLI from the project's root directory", file=sys.stderr)
    print("or that the modules are in your PYTHONPATH.", file=sys.stderr)
    sys.exit(1)


# Configure basic logging (config module also does this, but good to ensure it here for CLI)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SupagrokRAGCLI")

def handle_ingest(args):
    """Handles the 'ingest' command."""
    logger.info(f"Starting ingestion process for: {args.input_path}")
    try:
        config.ensure_openai_api_key() # Check API key early
        
        documents = doc_loader.load_documents(args.input_path)
        if not documents:
            logger.warning("No documents were loaded. Ingestion will not proceed.")
            print("No documents found or loaded. Please check the input path and file types.")
            return

        vector_store.create_and_persist_index(documents) # Uses default storage path from config
        logger.info("Ingestion process completed successfully.")
        print("Ingestion complete. Index created/updated in storage.")

    except FileNotFoundError as e:
        logger.error(f"Ingestion failed: {e}")
        print(f"Error: {e}. Please check the input path.")
    except ValueError as e: # Catch API key errors or other value errors
        logger.error(f"Ingestion failed due to configuration or value error: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during ingestion: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")

def handle_query(args):
    """Handles the 'query' command."""
    logger.info(f"Received query: '{args.query_text}'")
    try:
        config.ensure_openai_api_key() # Check API key early

        # Get query engine (will load default index)
        q_engine = query_engine.get_query_engine()
        if not q_engine:
            # Error message already logged by get_query_engine
            print("Could not initialize query engine. Has data been ingested?")
            return

        answer = query_engine.execute_query(args.query_text, q_engine)
        
        logger.info("Query processed.")
        print("\nAnswer:")
        print("------")
        print(answer if answer is not None else "No answer received or an error occurred.")
        print("------")

    except ValueError as e: # Catch API key errors
        logger.error(f"Query failed due to configuration or value error: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during query: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="Supagrok RAG System CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents into the vector store.")
    ingest_parser.add_argument("input_path", type=str, help="Path to the document file or directory to ingest.")
    ingest_parser.set_defaults(func=handle_ingest)

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the ingested documents.")
    query_parser.add_argument("query_text", type=str, help="The query text to ask the RAG system.")
    query_parser.set_defaults(func=handle_query)

    if len(sys.argv) == 1: # No command provided
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    
    logger.info(f"Executing command: {args.command}")
    args.func(args)

if __name__ == "__main__":
    main()
