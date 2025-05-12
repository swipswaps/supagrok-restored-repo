#!/usr/bin/env bash
# PRF-SUPAGROK-MASTERSETUP-2025-05-10
# UUID: master-orchestrator-uuid-20250510-002
# Timestamp: 2025-05-10T20:30:00Z
# Last Modified: 2025-05-10T21:00:00Z
# Description: (/opt/supagrok/orchestrate_supagrok_setup.sh) Master script to set up the Supagrok RAG system (including tests) and then kickstart the n8n Code Translation Hub project.
# Dependencies: System: sudo, apt-get (or compatible), python3, python3-pip, python3-venv (or equivalent like python3-devel), git, yt-dlp, Docker, Docker Compose, Node.js, npm/yarn (for n8n hub frontend dev).
# Inputs: Prompts for OpenAI API Key for RAG system.
# Outputs: Creates RAG project, n8n hub project, installs dependencies, configures .env files, runs RAG tests. Logs output to console.
# Version: 1.0.1
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

set -euo pipefail

# --- Configuration ---
# RAG System Configuration
RAG_PROJECT_PARENT_DIR="/opt/supagrok"
RAG_PROJECT_NAME="supagrok_rag_system_v2_final" # Matches Python script headers
RAG_PROJECT_DIR="${RAG_PROJECT_PARENT_DIR}/${RAG_PROJECT_NAME}"
RAG_PYTHON_EXEC="python3"
RAG_PIP_EXEC="pip3"
RAG_VENV_DIR_NAME="venv_rag"
RAG_REQUIREMENTS_FILE="requirements_rag.txt"
RAG_ENV_FILE=".env_rag_system" # Specific name for RAG .env
RAG_TEST_DATA_DIR="test_data_rag"
RAG_TEST_DOC_NAME="sample_rag_test_doc.txt"
RAG_TEST_YOUTUBE_URL="https://www.youtube.com/watch?v=z_LGan-t2Mo"

# n8n Hub Kickstart Configuration
N8N_HUB_KICKSTART_SCRIPT_DIR="/opt/supagrok/kickstarts" # Where the kickstart script itself will be placed
N8N_HUB_KICKSTART_SCRIPT_NAME="kickstart_supagrok_n8n_translator.sh"
N8N_HUB_KICKSTART_SCRIPT_PATH="${N8N_HUB_KICKSTART_SCRIPT_DIR}/${N8N_HUB_KICKSTART_SCRIPT_NAME}"
N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART="/home/owner/supagrok-tipiservice" # Kickstart script will be run from here

# --- Helper Functions ---
log_info() { echo "[INFO] $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
log_success() { echo "[SUCCESS] $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
log_warning() { echo "[WARNING] $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo "[ERROR] $(date +'%Y-%m-%d %H:%M:%S') - $1" >&2; }
command_exists() { command -v "$1" &> /dev/null; }

install_system_package() {
    local package_name="$1"
    local friendly_name="${2:-$1}"
    # This function now assumes the package_name is correct for the detected OS,
    # or it's a general name like 'git'. Specific logic for 'venv' is handled outside.
    if ! command_exists "$package_name"; then
        # If it's a command like 'git', check for the command.
        # If it's a package name like 'python3-pip', this check might not be perfect
        # but the install attempt will clarify.
        log_info "Attempting to install system dependency: ${friendly_name} (package: ${package_name})..."
        local installed_successfully=false
        if command_exists apt-get; then
            if sudo apt-get update && sudo apt-get install -y "$package_name"; then
                log_success "Successfully installed ${friendly_name} (package: ${package_name}) using apt-get."
                installed_successfully=true
            fi
        elif command_exists yum; then # Covers dnf as well on modern Fedora/Nobara
             if sudo yum install -y "$package_name"; then
                log_success "Successfully installed ${friendly_name} (package: ${package_name}) using yum/dnf."
                installed_successfully=true
             fi
        elif command_exists brew; then # macOS
             if brew install "$package_name"; then
                log_success "Successfully installed ${friendly_name} (package: ${package_name}) using Homebrew."
                installed_successfully=true
             fi
        fi

        if ! $installed_successfully; then # Check if any install method succeeded
            # Re-check command existence after install attempt
            if ! command_exists "$package_name"; then # If it's a command
                 # For packages like python3-pip, this check is less direct.
                 # A more robust check would be `pip3 --version` after attempting to install python3-pip.
                log_warning "Automatic installation of ${friendly_name} failed or package still not providing command '${package_name}'."
                if [ -f /etc/os-release ]; then
                    # shellcheck source=/dev/null
                    source /etc/os-release
                    log_warning "Detected OS ID: ${ID:-unknown}, Version: ${VERSION_ID:-unknown}."
                    log_warning "Please try installing '${package_name}' (or its equivalent for ${ID}) manually."
                else
                    log_warning "Could not determine OS distribution. Please install '${package_name}' manually."
                fi
                log_error "Cannot proceed without ${friendly_name}. Exiting."
                exit 1
            else
                log_info "${friendly_name} ('$package_name') command confirmed available after installation attempt."
            fi
        fi
    else
        log_info "${friendly_name} ('$package_name') is already installed/available."
    fi
}

# --- Main Orchestration Logic ---
main_orchestrator() {
    log_info "===== Starting Supagrok Master Orchestration Setup ====="

    # --- Phase 1: RAG System Setup ---
    log_info "--- Phase 1: Setting up Supagrok RAG System ---"
    setup_rag_system
    log_info "--- Phase 1: Supagrok RAG System Setup Complete ---"

    # --- Phase 2: n8n Code Translation Hub Kickstart ---
    log_info "--- Phase 2: Kickstarting n8n Code Translation Hub ---"
    kickstart_n8n_hub
    log_info "--- Phase 2: n8n Code Translation Hub Kickstart Complete ---"

    log_success "===== Supagrok Master Orchestration Setup Finished ====="
    log_info "Please review the output above for details and follow any manual configuration steps mentioned (especially for the n8n Hub's .env file)."
}

# --- RAG System Setup Function ---
setup_rag_system() {
    log_info "Target RAG project directory: ${RAG_PROJECT_DIR}"

    # 1. Sudo check
    log_info "Checking for sudo access (for RAG system dependencies)..."
    if [[ $EUID -ne 0 ]]; then
        if ! command_exists sudo; then
            log_warning "'sudo' command not found. If system dependencies for RAG are not installed, this phase may fail."
        else
            if ! sudo -v; then
                log_error "Sudo password incorrect or access denied. Cannot install RAG system dependencies."
                exit 1
            fi
        fi
    fi
    log_info "Sudo access for RAG setup verified (or not needed if root)."

    # 2. Install RAG System Dependencies
    log_info "Checking and installing RAG system dependencies..."
    install_system_package "${RAG_PYTHON_EXEC}" "Python 3 for RAG"
    install_system_package "python3-pip" "Python Pip for RAG"
    
    # Special handling for venv
    log_info "Checking for Python venv functionality ('${RAG_PYTHON_EXEC}' -m venv)..."
    if ! "${RAG_PYTHON_EXEC}" -m venv --help &> /dev/null; then
        log_warning "Python venv functionality ('${RAG_PYTHON_EXEC}' -m venv) not found or not working."
        local os_id_for_venv=""
        local os_pretty_name_for_venv="Unknown OS"
        if [ -f /etc/os-release ]; then
            os_id_for_venv=$(grep '^ID=' /etc/os-release | cut -d'=' -f2 | tr -d '"')
            os_pretty_name_for_venv=$(grep '^PRETTY_NAME=' /etc/os-release | cut -d'=' -f2 | tr -d '"')
        fi
        log_info "Attempting to install venv support for ${os_pretty_name_for_venv} (ID: ${os_id_for_venv})."

        local venv_pkg_installed=false
        if [[ "$os_id_for_venv" == "fedora" || "$os_id_for_venv" == "nobara" || "$os_id_for_venv" == "centos" || "$os_id_for_venv" == "rhel" || "$os_id_for_venv" == "almalinux" || "$os_id_for_venv" == "rocky" ]]; then
            log_info "On ${os_id_for_venv}, 'python3-devel' often provides full venv support. Attempting to install..."
            if sudo yum install -y python3-devel; then
                log_success "Installed 'python3-devel'."
                venv_pkg_installed=true
            else
                log_error "Failed to install 'python3-devel' on ${os_id_for_venv}."
            fi
        elif command_exists apt-get; then # Debian, Ubuntu, etc.
            log_info "On Debian-like system, 'python3-venv' package provides this. Attempting to install..."
            if sudo apt-get update && sudo apt-get install -y python3-venv; then
                 log_success "Installed 'python3-venv'."
                 venv_pkg_installed=true
            else
                log_error "Failed to install 'python3-venv' using apt-get."
            fi
        else
            log_warning "No specific venv package installation known for this OS. Assuming 'python3' should include it."
            # We will check again below.
        fi

        # Re-check venv functionality
        if ! "${RAG_PYTHON_EXEC}" -m venv --help &> /dev/null; then
            log_error "Python venv ('${RAG_PYTHON_EXEC}' -m venv) is still not available even after attempted package installation. Please ensure your Python 3 installation includes venv support. Exiting."
            exit 1
        else
            log_success "Python venv functionality confirmed after package installation attempt."
        fi
    else
        log_success "Python venv functionality ('${RAG_PYTHON_EXEC}' -m venv) is available."
    fi

    install_system_package "git" "Git"
    if ! command_exists yt-dlp; then
        log_warning "yt-dlp system package not found. Will install via pip into RAG venv."
    else
        log_info "yt-dlp (system-wide) found."
    fi
    log_success "RAG system dependency check complete."

    # 3. Create RAG Project Directory
    log_info "Setting up RAG project directory: ${RAG_PROJECT_DIR}"
    if [ -d "${RAG_PROJECT_DIR}" ]; then
        log_warning "RAG project directory ${RAG_PROJECT_DIR} already exists."
        read -r -p "RAG Setup: Remove existing RAG directory and proceed? (yes/NO): " confirm_remove_rag
        if [[ "${confirm_remove_rag,,}" == "yes" ]]; then
            log_info "Removing existing RAG directory: ${RAG_PROJECT_DIR}"
            sudo rm -rf "${RAG_PROJECT_DIR}"
        else
            log_error "RAG setup aborted. Please clear the directory or choose a different one."
            exit 1
        fi
    fi
    sudo mkdir -p "${RAG_PROJECT_DIR}"
    if [[ $EUID -ne 0 ]]; then 
        sudo chown -R "$(whoami):$(id -g -n "$(whoami)")" "${RAG_PROJECT_DIR}"
    fi
    
    local current_dir_before_rag_cd
    current_dir_before_rag_cd=$(pwd)
    cd "${RAG_PROJECT_DIR}"
    log_success "RAG project directory created and current directory changed to: $(pwd)"

    # 4. Setup RAG Python Virtual Environment
    log_info "Creating RAG Python virtual environment at ${RAG_PROJECT_DIR}/${RAG_VENV_DIR_NAME}..."
    "${RAG_PYTHON_EXEC}" -m venv "${RAG_VENV_DIR_NAME}"
    log_info "Activating RAG virtual environment..."
    # shellcheck source=/dev/null
    source "${RAG_VENV_DIR_NAME}/bin/activate"
    log_success "RAG Python virtual environment created and activated."

    log_info "Ensuring pip is up-to-date and installing yt-dlp via pip into RAG venv..."
    "${RAG_PIP_EXEC}" install --upgrade pip
    "${RAG_PIP_EXEC}" install yt-dlp 
    log_success "pip upgraded and yt-dlp installed in RAG venv."

    # 5. Generate RAG System Python Scripts
    log_info "Generating Supagrok RAG Python scripts into ${RAG_PROJECT_DIR}..."
    generate_rag_python_scripts 
    log_success "All RAG Python scripts generated."

    # 6. Generate RAG requirements.txt
    log_info "Generating ${RAG_PROJECT_DIR}/${RAG_REQUIREMENTS_FILE}..."
    generate_rag_requirements_file
    log_success "${RAG_REQUIREMENTS_FILE} generated."

    # 7. Install RAG Python Dependencies
    log_info "Installing RAG Python dependencies from ${RAG_REQUIREMENTS_FILE}..."
    if "${RAG_PIP_EXEC}" install -r "${RAG_REQUIREMENTS_FILE}"; then
        log_success "RAG Python dependencies installed successfully."
    else
        log_error "Failed to install RAG Python dependencies. Please check the output above."
        deactivate || true 
        cd "$current_dir_before_rag_cd" || true
        exit 1
    fi

    # 8. Handle RAG OpenAI API Key
    log_info "Configuring OpenAI API Key for RAG System..."
    local rag_openai_api_key=""
    while true; do
        read -s -r -p "Please enter your OpenAI API Key for the RAG System (starts with 'sk-', will not be shown): " rag_openai_api_key
        echo 
        if [[ "${rag_openai_api_key}" == sk-* ]] && [[ ${#rag_openai_api_key} -gt 30 ]]; then
            break
        else
            log_warning "Invalid OpenAI API Key format for RAG. It should start with 'sk-' and be longer. Please try again."
        fi
    done
    echo "OPENAI_API_KEY=\"${rag_openai_api_key}\"" > "${RAG_PROJECT_DIR}/${RAG_ENV_FILE}"
    chmod 600 "${RAG_PROJECT_DIR}/${RAG_ENV_FILE}"
    log_success "RAG OpenAI API Key saved to ${RAG_PROJECT_DIR}/${RAG_ENV_FILE} with restricted permissions."

    # 9. Prepare RAG Test Data
    log_info "Preparing RAG sample test data..."
    mkdir -p "${RAG_TEST_DATA_DIR}"
    echo "This is a Supagrok RAG system test document for automated setup." > "${RAG_TEST_DATA_DIR}/${RAG_TEST_DOC_NAME}"
    log_success "RAG sample test document created at ${RAG_PROJECT_DIR}/${RAG_TEST_DATA_DIR}/${RAG_TEST_DOC_NAME}"

    # 10. Run RAG Initial Tests
    log_info "--- Starting RAG System Initial Tests (within venv) ---"
    log_info "Test 1: Ingesting local text document for RAG..."
    if "${RAG_PYTHON_EXEC}" supagrok_rag_cli.py ingest "${RAG_TEST_DATA_DIR}/${RAG_TEST_DOC_NAME}"; then
        log_success "RAG Local document ingestion test completed."
    else
        log_error "RAG Local document ingestion test FAILED."
    fi

    log_info "Test 2: Ingesting YouTube video subtitles for RAG (${RAG_TEST_YOUTUBE_URL})..."
    if "${RAG_PYTHON_EXEC}" supagrok_rag_cli.py ingest "${RAG_TEST_YOUTUBE_URL}"; then
        log_success "RAG YouTube subtitle ingestion test completed."
    else
        log_error "RAG YouTube subtitle ingestion test FAILED."
    fi

    log_info "Test 3: Querying the RAG system..."
    local rag_test_query="What is this RAG system test document about?"
    log_info "RAG Query: ${rag_test_query}"
    if "${RAG_PYTHON_EXEC}" supagrok_rag_cli.py query "${rag_test_query}"; then
        log_success "RAG Query test completed. Review the answer above."
    else
        log_error "RAG Query test FAILED."
    fi
    log_info "--- RAG System Initial Tests Finished ---"

    log_info "Deactivating RAG virtual environment."
    deactivate || log_warning "Failed to deactivate RAG venv, or was not active."
    
    cd "$current_dir_before_rag_cd"
    log_info "Returned to directory: $(pwd)"
}

# --- n8n Hub Kickstart Function ---
kickstart_n8n_hub() {
    log_info "Preparing to kickstart n8n Code Translation Hub..."

    log_info "Ensuring n8n kickstart script directory exists: ${N8N_HUB_KICKSTART_SCRIPT_DIR}"
    sudo mkdir -p "${N8N_HUB_KICKSTART_SCRIPT_DIR}"
    if [[ $EUID -ne 0 ]]; then 
        sudo chown -R "$(whoami):$(id -g -n "$(whoami)")" "${N8N_HUB_KICKSTART_SCRIPT_DIR}"
    fi

    log_info "Generating n8n Hub kickstart script at ${N8N_HUB_KICKSTART_SCRIPT_PATH}..."
    generate_n8n_hub_kickstart_script 
    chmod +x "${N8N_HUB_KICKSTART_SCRIPT_PATH}"
    log_success "n8n Hub kickstart script generated and made executable."

    log_info "Checking for Docker and Docker Compose (required for n8n Hub)..."
    if ! command_exists docker; then
        log_error "Docker is not installed. The n8n Hub kickstart script requires Docker. Please install Docker and re-run."
        exit 1
    fi
    # Attempt to install docker-compose if not found
    if ! command_exists docker-compose; then
        log_warning "docker-compose command not found. Attempting to install..."
        if command_exists apt-get; then
            sudo apt-get update && sudo apt-get install -y docker-compose || log_error "Failed to install docker-compose via apt-get."
        elif command_exists yum; then
            sudo yum install -y docker-compose || log_error "Failed to install docker-compose via yum/dnf."
        elif command_exists brew; then
            brew install docker-compose || log_error "Failed to install docker-compose via brew."
        else
            log_error "Cannot determine how to install docker-compose. Please install it manually."
        fi
        if ! command_exists docker-compose; then
            log_error "Docker Compose is still not installed after attempt. Please install it manually and re-run."
            exit 1
        fi
    fi
    log_info "Docker and Docker Compose found/installed."

    log_info "Executing n8n Hub kickstart script from: ${N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART}"
    log_info "The n8n Hub project will be created in a subdirectory of: ${N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART}"
    
    # Ensure the parent directory for the kickstart script's execution context exists
    # This is where the kickstart script will create its 'supagrok_n8n_code_translator' subdir
    if [ ! -d "${N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART}" ]; then
        log_info "Creating parent directory for n8n Hub project: ${N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART}"
        # This might require sudo if it's outside user's home, e.g. /opt/
        # For /home/owner/supagrok-tipiservice, current user should have rights.
        mkdir -p "${N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART}" || { 
            log_error "Failed to create ${N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART}. Check permissions."; exit 1; 
        }
    fi
    
    # Execute the kickstart script from the N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART directory
    # so that its SCRIPT_DIR_KICKSTART resolves correctly and it creates the project there.
    (cd "${N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART}" && "${N8N_HUB_KICKSTART_SCRIPT_PATH}")
    
    log_success "n8n Hub kickstart script execution finished."
    log_info "IMPORTANT FOR N8N HUB:"
    log_info "1. Navigate to the n8n hub project directory ('${N8N_HUB_PROJECT_PARENT_DIR_FOR_KICKSTART}/supagrok_n8n_code_translator/')."
    log_info "2. CRITICALLY review and EDIT the '.env' file in that directory with your database passwords and other secrets."
    log_info "3. Then, run 'docker-compose up -d' in that directory to start n8n and Supabase services."
}


# --- Function to Generate RAG Python Scripts (into current RAG_PROJECT_DIR) ---
generate_rag_python_scripts() {
    # File 1: supagrok_rag_config.py
    cat << EOF > "${RAG_PROJECT_DIR}/supagrok_rag_config.py"
#!/usr/bin/env python3
# PRF-SUPAGROK-RAGCONFIG-2025-05-10
# UUID: cfg-a1b2c3d4-e5f6-7890-1234-567890abcdef 
# Timestamp: 2025-05-10T21:00:00Z
# Last Modified: 2025-05-10T21:00:00Z 
# Description: (${RAG_PROJECT_NAME}/supagrok_rag_config.py) Configuration settings for the Supagrok RAG system. Handles API keys, storage paths, and other system parameters.
# Dependencies: python-dotenv, os, pathlib, typing
# Inputs: ${RAG_ENV_FILE} file in CWD (expected to contain OPENAI_API_KEY)
# Outputs: Configuration variables (API key, storage path, preferred languages)
# Version: 1.3.2 
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import List, Optional as TypingOptional 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

env_path_rag_specific = Path.cwd() / "${RAG_ENV_FILE}"

if env_path_rag_specific.is_file():
    logger.info(f"Loading ${RAG_ENV_FILE} file from: {env_path_rag_specific}")
    load_dotenv(dotenv_path=env_path_rag_specific)
else:
    logger.warning(f"${RAG_ENV_FILE} file not found at {env_path_rag_specific}. Relying on environment variables.")
    load_dotenv() 


OPENAI_API_KEY_CONFIG: TypingOptional[str] = os.getenv("OPENAI_API_KEY")

STORAGE_DIR_NAME_CONFIG: str = "supagrok_rag_storage_v2_final" 
STORAGE_DIR_CONFIG_PATH: Path = Path.cwd() / STORAGE_DIR_NAME_CONFIG

YOUTUBE_PREFERRED_SUBTITLE_LANGS_CONFIG: List[str] = ['en', 'en-US', 'en-GB', 'en-AU', 'en-CA']


def ensure_openai_api_key() -> None:
    if not OPENAI_API_KEY_CONFIG:
        msg = f"OPENAI_API_KEY not found. Please set it in your ${RAG_ENV_FILE} file or environment."
        logger.error(msg)
        raise ValueError(msg)
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY_CONFIG 
    logger.info("OpenAI API key loaded and verified from configuration.")

def get_storage_path() -> Path:
    STORAGE_DIR_CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    return STORAGE_DIR_CONFIG_PATH

def get_youtube_preferred_subtitle_langs() -> List[str]:
    return YOUTUBE_PREFERRED_SUBTITLE_LANGS_CONFIG

if __name__ == "__main__":
    logger.info("Configuration module self-test:")
    try:
        ensure_openai_api_key()
        logger.info("OpenAI API Key check passed (key presence verified).")
    except ValueError as e:
        logger.error(f"Configuration Self-Test Error: {e}")
    logger.info(f"Default vector store location: {get_storage_path()}")
    logger.info(f"Preferred YouTube subtitle languages: {get_youtube_preferred_subtitle_langs()}")
    logger.info("Configuration module self-test finished.")
EOF
    chmod +x "${RAG_PROJECT_DIR}/supagrok_rag_config.py"

    # File 2: supagrok_youtube_ingest_utils.py
    cat << EOF > "${RAG_PROJECT_DIR}/supagrok_youtube_ingest_utils.py"
#!/usr/bin/env python3
# PRF-SUPAGROK-RAGYOUTUBEUTILS-2025-05-10
# UUID: ytutil-b2c3d4e5-f6a7-8901-2345-67890abcde
# Timestamp: 2025-05-10T21:00:00Z
# Last Modified: 2025-05-10T21:00:00Z 
# Description: (${RAG_PROJECT_NAME}/supagrok_youtube_ingest_utils.py) Utilities for fetching YouTube video information and subtitles using yt-dlp for RAG ingestion.
# Dependencies: Python packages: None directly, uses subprocess. System dependencies: yt-dlp
# Inputs: YouTube video URL, preferred language codes.
# Outputs: Dictionary containing video title, cleaned subtitle text, URL, and language code.
# Version: 1.2.2
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import subprocess, pathlib, json, logging, tempfile, re, shutil, sys, os 
from typing import List, Optional as TypingOptional, Dict, Tuple, Any
logger = logging.getLogger(__name__)
YT_DLP_CMD_PATH_UTIL: str = "yt-dlp"; _yt_dlp_available_ytutil: TypingOptional[bool] = None

def check_yt_dlp_availability() -> bool:
    global _yt_dlp_available_ytutil, YT_DLP_CMD_PATH_UTIL
    if _yt_dlp_available_ytutil is None:
        yt_dlp_in_venv = Path(sys.executable).parent / "yt-dlp"
        if yt_dlp_in_venv.is_file() and os.access(yt_dlp_in_venv, os.X_OK):
            YT_DLP_CMD_PATH_UTIL = str(yt_dlp_in_venv); _yt_dlp_available_ytutil = True
            logger.info(f"Using yt-dlp from venv: {YT_DLP_CMD_PATH_UTIL}")
        elif shutil.which("yt-dlp"):
            YT_DLP_CMD_PATH_UTIL = shutil.which("yt-dlp"); _yt_dlp_available_ytutil = True
            logger.info(f"Using system yt-dlp: {YT_DLP_CMD_PATH_UTIL}")
        else: logger.error("'yt-dlp' not found."); _yt_dlp_available_ytutil = False
    return _yt_dlp_available_ytutil

def _run_yt_dlp_command(args: List[str]) -> Tuple[TypingOptional[str], TypingOptional[str], int]:
    if not check_yt_dlp_availability(): return None, f"'{YT_DLP_CMD_PATH_UTIL}' unavailable.", -1
    cmd = [YT_DLP_CMD_PATH_UTIL] + args; logger.debug(f"Running: {' '.join(cmd)}")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=180)
        if p.returncode != 0: logger.warning(f"yt-dlp failed (rc={p.returncode}): {p.stderr.strip() if p.stderr else 'No stderr'}")
        return p.stdout, p.stderr, p.returncode
    except Exception as e: logger.error(f"yt-dlp error: {e}", exc_info=True); return None, str(e), -1

def get_video_info(url: str) -> TypingOptional[Dict[str, Any]]:
    logger.info(f"Fetching info for: {url}"); args = ["--dump-json", "--no-warnings", "--skip-download", url]
    out, _, rc = _run_yt_dlp_command(args)
    if rc != 0 or not out: return None
    try: return json.loads(out)
    except json.JSONDecodeError: logger.error(f"JSON parse error for {url}"); return None

def _parse_vtt(content: str) -> str:
    no_tags = re.sub(r'<[^>]+>', '', content)
    lines = [l.strip() for l in no_tags.splitlines() if l.strip() and not (l.strip().upper()=="WEBVTT" or "-->" in l or re.fullmatch(r'\d+',l.strip()) or l.strip().startswith(("Kind:","Language:")))]
    return "\n".join([lines[0]] + [lines[i] for i in range(1, len(lines)) if lines[i] != lines[i-1]]) if lines else ""

def fetch_youtube_subtitle_text(url: str, langs: List[str]) -> TypingOptional[Dict[str, str]]:
    if not check_yt_dlp_availability(): return None
    info = get_video_info(url); title = info.get("title", "Unknown") if info else "Unknown"
    if not info: return None; logger.info(f"Processing: {title}")
    subs = []; flags = {"subtitles":"--write-sub", "automatic_captions":"--write-auto-sub"}
    for k, f in flags.items():
        for lang_code, fmts in info.get(k, {}).items():
            for fmt_info in fmts:
                if fmt_info.get('ext') == 'vtt': subs.append((lang_code, f, fmt_info))
    
    sel_opt = None
    for p_lang in langs + ['en']:
        for l_code, l_flag, _ in subs:
            if l_code.startswith(p_lang) and (sel_opt is None or l_flag == flags["subtitles"]):
                sel_opt = (l_code, l_flag);
                if l_flag == flags["subtitles"]: break
        if sel_opt and sel_opt[1] == flags["subtitles"]: break
    if not sel_opt and subs: sel_opt = (subs[0][0], subs[0][1])
    if not sel_opt: logger.warning(f"No VTT subs for {url}"); return None
    
    s_lang, s_flag = sel_opt; logger.info(f"Selected sub: lang='{s_lang}', type='{s_flag.split('-')[-1]}' for {url}")
    with tempfile.TemporaryDirectory(prefix="sg_subs_") as tmp:
        out_tpl = str(pathlib.Path(tmp) / "sub.%(ext)s")
        cmd_dl = [s_flag, "--skip-download", "--sub-format", "vtt", "--sub-langs", s_lang, "-o", out_tpl, url]
        _, _, rc_dl = _run_yt_dlp_command(cmd_dl)
        if rc_dl != 0: logger.error(f"yt-dlp download failed for {url} (lang: {s_lang})"); return None
        dl_files = list(pathlib.Path(tmp).glob("*.vtt"))
        if not dl_files: logger.error(f"Sub file not found in {tmp} for {s_lang}"); return None
        try:
            txt = _parse_vtt(dl_files[0].read_text(encoding='utf-8'))
            if not txt.strip(): logger.warning(f"Subs for {url} (lang: {s_lang}) empty.")
            return {"title": title, "text": txt, "url": url, "language": s_lang}
        except Exception as e: logger.error(f"Read/parse error {dl_files[0]}: {e}", exc_info=True); return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    if not check_yt_dlp_availability(): sys.exit("FATAL: yt-dlp unavailable.")
    urls = ["https://www.youtube.com/watch?v=z_LGan-t2Mo", "https://www.youtube.com/watch?v=pNcQ5xxNl3E"]
    p_langs = ['en']; from supagrok_rag_config import get_youtube_preferred_subtitle_langs; p_langs = get_youtube_preferred_subtitle_langs()
    for u in urls: logger.info(f"--- Test: {u} ---"); d = fetch_youtube_subtitle_text(u, p_langs); logger.info(f"{'Success' if d else 'Failed'}: {d['title'] if d else u}, Lang: {d['language'] if d else 'N/A'}, Text: {d['text'][:100].strip() if d else 'N/A'}...")
    logger.info("YT ingest utils self-test done.")
EOF
    chmod +x "${RAG_PROJECT_DIR}/supagrok_youtube_ingest_utils.py"

    # File 3: supagrok_rag_document_loader.py
    cat << EOF > "${RAG_PROJECT_DIR}/supagrok_rag_document_loader.py"
#!/usr/bin/env python3
# PRF-SUPAGROK-RAGDOCLOADER-2025-05-10
# UUID: docload-c3d4e5f6-a7b8-9012-3456-7890abcdef
# Timestamp: 2025-05-10T21:00:00Z
# Last Modified: 2025-05-10T21:00:00Z 
# Description: (${RAG_PROJECT_NAME}/supagrok_rag_document_loader.py) Loads and parses documents from files, directories, or YouTube URLs for the RAG system.
# Dependencies: Python packages: llama_index.core. Uses supagrok_youtube_ingest_utils.
# Inputs: Path to a document, a directory of documents, or a YouTube video URL.
# Outputs: List of LlamaIndex Document objects.
# Version: 1.3.2
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

from pathlib import Path; import logging, re; from llama_index.core import SimpleDirectoryReader, Document; from typing import List
import supagrok_youtube_ingest_utils, supagrok_rag_config
logger = logging.getLogger(__name__)
YT_URL_PAT = re.compile(r"^(https?://)?(www\.)?(youtube\.com/(watch\?v=|embed/|shorts/|live/)|youtu\.be/)([a-zA-Z0-9_-]{11}).*$")

def _is_yt_url(s: str) -> bool: return YT_URL_PAT.match(s) is not None
def _load_from_yt(url: str) -> List[Document]:
    logger.info(f"Loading from YT: {url}"); langs = supagrok_rag_config.get_youtube_preferred_subtitle_langs()
    data = supagrok_youtube_ingest_utils.fetch_youtube_subtitle_text(url, langs)
    if data and data["text"] and data["text"].strip():
        meta = {"source_type":"youtube_video_subtitles", "video_title":data.get("title","?"), "video_url":data.get("url",url), "subtitle_language_code":data.get("language","?"), "original_input_source":url, "content_length_chars":len(data["text"])}
        logger.info(f"Created LlamaIndex Doc from YT: {url} (Title: {meta['video_title']})")
        return [Document(text=data["text"], metadata=meta, doc_id=f"youtube_{url}")]
    logger.warning(f"No valid subs for YT: {url}"); return []

def load_documents(src: str) -> List[Document]:
    if not src or not src.strip(): raise ValueError("Input source empty.")
    if _is_yt_url(src): return _load_from_yt(src)
    p = Path(src);
    if not p.exists(): raise FileNotFoundError(f"Path not found: {p}")
    logger.info(f"Loading from local: {p}")
    try:
        if p.is_file(): docs = SimpleDirectoryReader(input_dir=str(p.parent), input_files=[p.name]).load_data(); logger.info(f"Loaded 1 doc: {p.name}")
        elif p.is_dir(): docs = SimpleDirectoryReader(input_dir=str(p), recursive=True).load_data(); logger.info(f"Loaded {len(docs)} docs from dir: {p}")
        else: raise ValueError(f"Not recognized type: {p}")
        if not docs: logger.warning(f"No docs from {p}.")
        return docs
    except Exception as e: logger.error(f"Load failed {p}: {e}", exc_info=True); raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO); test_d = Path.cwd()/"test_dl_orch"; test_d.mkdir(exist_ok=True)
    (test_f := test_d/"s_orch.txt").write_text("Local test for orchestrator.")
    logger.info(f"--- File test: {test_f} ---"); [logger.info(f"FileDoc: {d.doc_id}, Txt: {d.text[:30]}..., Meta: {d.metadata}") for d in load_documents(str(test_f))]
    yt = "https://www.youtube.com/watch?v=z_LGan-t2Mo"; logger.info(f"--- YT test: {yt} ---")
    if supagrok_youtube_ingest_utils.check_yt_dlp_availability(): [logger.info(f"YTDoc: {d.doc_id}, Title: {d.metadata.get('video_title')}, Txt: {d.text[:30]}..., Meta: {d.metadata}") for d in load_documents(yt)]
    else: logger.warning("yt-dlp unavailable, skipping YT test.")
    logger.info("Doc loader self-test done. Cleanup 'test_dl_orch' if needed.")
EOF
    chmod +x "${RAG_PROJECT_DIR}/supagrok_rag_document_loader.py"

    # File 4: supagrok_rag_vector_store.py
    cat << EOF > "${RAG_PROJECT_DIR}/supagrok_rag_vector_store.py"
#!/usr/bin/env python3
# PRF-SUPAGROK-RAGVECTORSTORE-2025-05-10
# UUID: vecstore-d4e5f6a7-b8c9-0123-4567-890abcde
# Timestamp: 2025-05-10T21:00:00Z
# Last Modified: 2025-05-10T21:00:00Z 
# Description: (${RAG_PROJECT_NAME}/supagrok_rag_vector_store.py) Manages the LlamaIndex vector store for the RAG system.
# Dependencies: Python packages: llama_index.core, llama_index.llms.openai, llama_index.embeddings.huggingface. Uses supagrok_rag_config.
# Inputs: List of LlamaIndex Document objects for ingestion, storage path.
# Outputs: Creates/updates a vector index on disk. Loads an index from disk.
# Version: 1.2.2
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import logging; from pathlib import Path; from typing import List, Optional as Opt
from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from llama_index.llms.openai import OpenAI; from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import supagrok_rag_config as cfg; logger = logging.getLogger(__name__)
try:
    cfg.ensure_openai_api_key(); Settings.llm=OpenAI(model="gpt-3.5-turbo",temperature=0.1); Settings.embed_model=HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    logger.info(f"LLM: {Settings.llm.metadata.model_name}, Embed: {Settings.embed_model.model_name}")
except Exception as e: logger.critical(f"LLamaIndex Settings Err: {e}",exc_info=True); raise

def create_and_persist_index(docs: List[Document], p_dir_ovr: Opt[Path]=None) -> VectorStoreIndex:
    if not docs: raise ValueError("No docs for index.")
    p_dir = p_dir_ovr or cfg.get_storage_path(); p_dir.mkdir(parents=True,exist_ok=True)
    logger.info(f"Creating index in {p_dir} ({len(docs)} docs).")
    try: idx=VectorStoreIndex.from_documents(docs,show_progress=True); idx.storage_context.persist(str(p_dir)); logger.info(f"Index persisted: {p_dir}"); return idx
    except Exception as e: logger.error(f"Index create/persist fail {p_dir}: {e}",exc_info=True); raise

def load_persisted_index(p_dir_ovr: Opt[Path]=None) -> Opt[VectorStoreIndex]:
    p_dir = p_dir_ovr or cfg.get_storage_path()
    if not (p_dir.exists() and any(p_dir.iterdir())): logger.warning(f"Index dir {p_dir} missing/empty."); return None
    logger.info(f"Loading index from: {p_dir}")
    try: s_ctx=StorageContext.from_defaults(str(p_dir)); idx=load_index_from_storage(s_ctx); logger.info(f"Index loaded: {p_dir}"); return idx
    except Exception as e: logger.error(f"Index load fail {p_dir}: {e}",exc_info=True); return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO); logger.info("VS self-test.")
    try:
        ds=[Document(text="D1 VS test."),Document(text="D2 VS test.")]; t_s_d=Path.cwd()/"test_rag_sto_v2f_vs_orch2"
        if t_s_d.exists(): import shutil; shutil.rmtree(t_s_d)
        logger.info("--- Idx create ---"); i=create_and_persist_index(ds,p_dir_ovr=t_s_d)
        if i: logger.info(f"Idx created, docs: {len(i.docstore.docs)}")
        logger.info("--- Idx load ---"); l_i=load_persisted_index(p_dir_ovr=t_s_d)
        if l_i: logger.info(f"Idx loaded, docs: {len(l_i.docstore.docs)}"); print(f"Test Q: {l_i.as_query_engine().query('What is D1 about?')}")
        else: logger.warning("Could not load index.")
    except Exception as e: logger.error(f"VS Test FAIL: {e}",exc_info=True)
    logger.info("VS self-test done. Cleanup 'test_rag_sto_v2f_vs_orch2' if needed.")
EOF
    chmod +x "${RAG_PROJECT_DIR}/supagrok_rag_vector_store.py"

    # File 5: supagrok_rag_query_engine.py
    cat << EOF > "${RAG_PROJECT_DIR}/supagrok_rag_query_engine.py"
#!/usr/bin/env python3
# PRF-SUPAGROK-RAGQUERYENGINE-2025-05-10
# UUID: queryeng-e5f6a7b8-c9d0-1234-5678-90abcdef
# Timestamp: 2025-05-10T21:00:00Z
# Last Modified: 2025-05-10T21:00:00Z 
# Description: (${RAG_PROJECT_NAME}/supagrok_rag_query_engine.py) Handles querying the RAG vector index using LlamaIndex.
# Dependencies: Python packages: llama_index.core. Uses supagrok_rag_vector_store, supagrok_rag_config.
# Inputs: Query string, LlamaIndex VectorStoreIndex object (optional).
# Outputs: Query response string.
# Version: 1.2.2
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import logging; from pathlib import Path; from typing import Optional as Opt
from llama_index.core import VectorStoreIndex; from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.response.schema import RESPONSE_TYPE as LlamaResp
import supagrok_rag_vector_store as vs, supagrok_rag_config as cfg; logger=logging.getLogger(__name__)

def get_query_engine(idx_inst: Opt[VectorStoreIndex]=None) -> Opt[BaseQueryEngine]:
    try: cfg.ensure_openai_api_key()
    except ValueError as e: logger.error(f"API key err for QE: {e}"); return None
    idx = idx_inst or vs.load_persisted_index()
    if not idx: logger.error("No index for QE."); return None
    logger.info("Creating QE...");
    try: qe=idx.as_query_engine(similarity_top_k=3,streaming=False); logger.info("QE created."); return qe
    except Exception as e: logger.error(f"QE create fail: {e}",exc_info=True); return None

def execute_query(q_txt: str, qe_inst: Opt[BaseQueryEngine]=None) -> Opt[str]:
    qe = qe_inst or get_query_engine()
    if not qe: return "Err: QE unavailable."
    if not q_txt or not q_txt.strip(): return "Query empty."
    logger.info(f"Query: '{q_txt}'")
    try:
        resp: LlamaResp = qe.query(q_txt); logger.info("Query done.")
        return str(resp.response) if hasattr(resp,'response') else str(resp)
    except Exception as e:
        logger.error(f"Query err: {e}",exc_info=True); err_s=str(e).upper()
        if any(k in err_s for k in ["API KEY","AUTHENTICATION","RATE LIMIT"]): return f"Err (API issue): {e}"
        return f"Query err: {e}"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO); logger.info("QE self-test.")
    try:
        t_idx_p=Path.cwd()/"test_rag_sto_v2f_vs_orch2"; logger.info(f"Loading index from {t_idx_p} for QE test.")
        t_idx=vs.load_persisted_index(p_dir_ovr=t_idx_p)
        if t_idx:
            q_e=get_query_engine(idx_inst=t_idx)
            if q_e: q="What is D1 about?"; logger.info(f"Test Q: '{q}'"); print(f"Test Ans: {execute_query(q, q_e)}")
            else: logger.error("No QE from test index.")
        else: logger.warning(f"No test index from '{t_idx_p}'. Run VS test first.")
    except Exception as e: logger.error(f"QE Test FAIL: {e}",exc_info=True)
    logger.info("QE self-test done.")
EOF
    chmod +x "${RAG_PROJECT_DIR}/supagrok_rag_query_engine.py"

    # File 6: supagrok_rag_cli.py
    cat << EOF > "${RAG_PROJECT_DIR}/supagrok_rag_cli.py"
#!/usr/bin/env python3
# PRF-SUPAGROK-RAGCLI-2025-05-10
# UUID: cli-f6a7b8c9-d0e1-2345-6789-0abcdef012
# Timestamp: 2025-05-10T21:00:00Z
# Last Modified: 2025-05-10T21:00:00Z 
# Description: (${RAG_PROJECT_NAME}/supagrok_rag_cli.py) Command Line Interface for the Supagrok RAG system. Handles ingestion from files, directories, or YouTube URLs, and querying.
# Dependencies: Python packages: argparse. Uses local supagrok_rag_* modules.
# Inputs: Command-line arguments for ingestion or querying.
# Outputs: Console output (status messages, query responses, errors).
# Version: 1.3.2
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import argparse, logging, sys; from pathlib import Path
try:
    import supagrok_rag_config as cfg; import supagrok_rag_vector_store as vs
    import supagrok_rag_document_loader as dl; import supagrok_rag_query_engine as qe
except Exception as e: print(f"CRIT CLI Import Err: {e}. Check modules & .env.",file=sys.stderr); sys.exit(1)
logging.basicConfig(level=logging.INFO,format='%(asctime)s-%(name)s-%(levelname)s-%(message)s'); logger=logging.getLogger("SupagrokRAG_CLI")

def h_ingest(args: argparse.Namespace):
    logger.info(f"Ingesting: '{args.input_source}'")
    try:
        cfg.ensure_openai_api_key(); logger.info("Loading docs...")
        docs=dl.load_documents(args.input_source)
        if not docs: logger.warning("No docs loaded."); return
        logger.info(f"Loaded {len(docs)} docs. Indexing..."); vs.create_and_persist_index(docs)
        print(f"\n✅ Ingest done. Index: {cfg.get_storage_path()}")
    except Exception as e: logger.error(f"Ingest fail: {e}",exc_info=True); print(f"Ingest Err: {e}")

def h_query(args: argparse.Namespace):
    logger.info(f"Query: '{args.query_text}'")
    try:
        cfg.ensure_openai_api_key(); q_eng=qe.get_query_engine()
        if not q_eng: print("Err: No QE."); return
        ans=qe.execute_query(args.query_text, q_eng)
        print(f"\n🤖 Supagrok Ans:\n{'='*40}\n{ans or 'No ans.'}\n{'='*40}")
    except Exception as e: logger.error(f"Query fail: {e}",exc_info=True); print(f"Query Err: {e}")

def main_cli():
    p=argparse.ArgumentParser(description="Supagrok RAG CLI.",formatter_class=argparse.RawTextHelpFormatter)
    s=p.add_subparsers(dest="command",help="Cmds: ingest, query",required=True)
    i_p=s.add_parser("ingest",help="Ingest docs.");i_p.add_argument("input_source",type=str,help="File/dir/YT URL");i_p.set_defaults(func=h_ingest)
    q_p=s.add_parser("query",help="Query docs.");q_p.add_argument("query_text",type=str,help="Question");q_p.set_defaults(func=h_query)
    if len(sys.argv)==1: p.print_help(sys.stderr); sys.exit(1)
    a=p.parse_args(); logger.info(f"CLI: Cmd '{a.command}'...")
    if hasattr(a,'func'): a.func(a)
    else: logger.error("CLI internal err: No func."); p.print_help(sys.stderr); sys.exit(1)
    logger.info(f"Cmd '{a.command}' done.")
if __name__=="__main__": main_cli()
EOF
    chmod +x "${RAG_PROJECT_DIR}/supagrok_rag_cli.py"
}

# --- Function to Generate RAG requirements.txt (into current RAG_PROJECT_DIR) ---
generate_rag_requirements_file() {
    cat << EOF > "${RAG_PROJECT_DIR}/${RAG_REQUIREMENTS_FILE}"
# PRF-SUPAGROK-RAGREQ-2025-05-10
# UUID: rag-requirements-uuid-20250510-final-orchestrated-v2
# Timestamp: 2025-05-10T21:00:00Z
# Description: (${RAG_PROJECT_NAME}/${RAG_REQUIREMENTS_FILE}) Python dependencies for the Supagrok RAG system.
# Version: 1.0.3
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

python-dotenv>=1.0.0
llama-index>=0.10.0,<0.11.0
llama-index-llms-openai>=0.1.5
openai>=1.3.0
llama-index-embeddings-huggingface>=0.1.4
sentence-transformers>=2.2.2
# yt-dlp is installed by this master setup script's RAG venv setup phase directly via pip.
# Listing it here is for documentation; it will be installed before this file is used by pip.
yt-dlp>=2023.07.06 
EOF
}

# --- Function to Generate n8n Hub Kickstart Script (into N8N_HUB_KICKSTART_SCRIPT_PATH) ---
generate_n8n_hub_kickstart_script() {
    cat << 'KICKSTARTEOF' > "${N8N_HUB_KICKSTART_SCRIPT_PATH}"
#!/usr/bin/env bash
# PRF-SUPAGROK-KICKSTARTSCRIPT-2025-05-10
# UUID: 7b8c0d2e-4f6a-88b9-c0d1-e2f3g4h5i6j7
# Timestamp: 2025-05-10T21:00:00Z
# Last Modified: 2025-05-10T21:00:00Z 
# Description: (kickstart_supagrok_n8n_translator.sh) One-shot script to kickstart the Supagrok n8n Code Translator project structure. Path in description is relative to where it's run.
# Dependencies: Docker, Docker Compose, Node.js, npm/yarn.
# Inputs: None. Creates a subdirectory in its execution directory.
# Outputs: Creates 'supagrok_n8n_code_translator' project directory.
# Version: 1.0.3
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

set -euo pipefail
SCRIPT_DIR_KICKSTART="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_NAME_HUB="supagrok_n8n_code_translator" 
PROJECT_DIR_TARGET_HUB="${SCRIPT_DIR_KICKSTART}/${PROJECT_NAME_HUB}"

_ks_log_info() { echo "[KS INFO] $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
_ks_log_success() { echo "[KS SUCCESS] $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
_ks_log_error() { echo "[KS ERROR] $(date +'%Y-%m-%d %H:%M:%S') - $1" >&2; }

_ks_main() {
    _ks_log_info "Starting Supagrok n8n Code Translator Hub kickstart..."
    _ks_log_info "This script will create the project in: ${PROJECT_DIR_TARGET_HUB}"
    if [ -d "${PROJECT_DIR_TARGET_HUB}" ]; then
        read -r -p "n8n Hub Kickstart: Project directory '${PROJECT_DIR_TARGET_HUB}' already exists. Remove and recreate? (yes/NO): " confirm_remove_hub
        if [[ "${confirm_remove_hub,,}" == "yes" ]];
            then _ks_log_info "Removing existing n8n Hub directory: ${PROJECT_DIR_TARGET_HUB}"; rm -rf "${PROJECT_DIR_TARGET_HUB}";
            else _ks_log_error "n8n Hub project dir exists. Aborting kickstart."; exit 1;
        fi
    fi
    mkdir -p "${PROJECT_DIR_TARGET_HUB}"; cd "${PROJECT_DIR_TARGET_HUB}"
    _ks_log_info "Created n8n Hub project directory: $(pwd)"
    _ks_create_docker_compose; _ks_create_python_placeholders; _ks_create_react_frontend; _ks_create_readme
    _ks_log_success "n8n Hub Project kickstart complete for '${PROJECT_NAME_HUB}' at: ${PROJECT_DIR_TARGET_HUB}"
    _ks_log_info "Next steps for n8n Hub: 1. Review files. 2. IMPORTANT: Configure '.env' in '${PROJECT_DIR_TARGET_HUB}'. 3. Start services: cd '${PROJECT_DIR_TARGET_HUB}' && docker-compose up -d"
}

_ks_create_docker_compose() {
    _ks_log_info "Creating n8n Hub docker-compose.yml and .env.example..."
    mkdir -p "./config/n8n_data"; mkdir -p "./config/supabase_db_data"
    cat << 'DCEOF' > "./docker-compose.yml"
# PRF-SUPAGROK-DOCKERCOMPOSE-N8NTRANSLATOR-20250510
# UUID: dc-n8n-translator-uuid-20250510-001
# Timestamp: 2025-05-10T21:00:00Z
# Description: (supagrok_n8n_code_translator/docker-compose.yml) Docker Compose for n8n Hub.
# Version: 1.1.1; Author: SupagrokAgent/1.5; PRF-Codex-Version: 1.7
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest; container_name: supagrok_n8n_translator_n8n; restart: unless-stopped
    ports: ["\-5678:5678"]
    environment:
      - N8N_HOST=\-localhost; - N8N_PORT=5678; - N8N_PROTOCOL=\-http
      - NODE_ENV=\-production; - WEBHOOK_URL=\-http://localhost:\-5678/
      - GENERIC_TIMEZONE=\-America/New_York
      - DB_POSTGRESDB_HOST=supagrok_n8n_translator_supabase_db
      - DB_POSTGRESDB_DATABASE=\-supagrok_translator_db
      - DB_POSTGRESDB_USER=\-supagrok_translator_user
      - DB_POSTGRESDB_PASSWORD=\-YourSupabaseDbPassword
      - DB_POSTGRESDB_PORT=5432; - DB_POSTGRESDB_SSL_ENABLED=false
    volumes: ["./config/n8n_data:/home/node/.n8n"]
    depends_on: {supabase_db: {condition: service_healthy}}
  supabase_db:
    image: postgres:15-alpine; container_name: supagrok_n8n_translator_supabase_db; restart: unless-stopped
    ports: ["\-54322:5432"]
    environment:
      - POSTGRES_USER=\-supagrok_translator_user
      - POSTGRES_PASSWORD=\-YourSupabaseDbPassword
      - POSTGRES_DB=\-supagrok_translator_db
    volumes: ["./config/supabase_db_data:/var/lib/postgresql/data"]
    healthcheck: {test: ["CMD-SHELL", "pg_isready -U \$${POSTGRES_USER:-supagrok_translator_user} -d \$${POSTGRES_DB:-supagrok_translator_db}"], interval: 10s, timeout: 5s, retries: 5}
  supabase_studio:
    image: supabase/studio:latest; container_name: supagrok_n8n_translator_supabase_studio; restart: unless-stopped
    ports: ["\-8001:3000"]
    environment:
      - SUPABASE_URL=http://localhost:\-8001 
      - SUPABASE_DB_HOST=supagrok_n8n_translator_supabase_db; - SUPABASE_DB_PORT=5432
      - SUPABASE_DB_USER=\-supagrok_translator_user
      - SUPABASE_DB_PASSWORD=\-YourSupabaseDbPassword
      - SUPABASE_DB_NAME=\-supagrok_translator_db
      - SUPABASE_PUBLIC_URL=http://localhost:\-8001
    depends_on: {supabase_db: {condition: service_healthy}}
volumes: {n8n_data_vol_persistent: {}, supabase_db_data_vol_persistent: {}}
DCEOF
    cat << 'ENVEXEOF' > "./.env.example"
# PRF-SUPAGROK-ENVEX-N8NTRANSLATOR-20250510
# UUID: env-ex-n8n-translator-uuid-20250510-001; Timestamp: 2025-05-10T21:00:00Z
# Description: (supagrok_n8n_code_translator/.env.example) Example .env for n8n Hub.
# Version: 1.1.1; Author: SupagrokAgent/1.5; PRF-Codex-Version: 1.7
TZ=America/New_York; NODE_ENV=production
N8N_HOST_PORT=5678; N8N_HOST_DOMAIN=localhost; N8N_PROTOCOL=http
N8N_WEBHOOK_URL=http://\-localhost:\-5678/
POSTGRES_USER=supagrok_translator_admin
POSTGRES_PASSWORD=a_very_secure_password_CHANGE_THIS
POSTGRES_DB=supagrok_translator_db
POSTGRES_HOST_PORT=54322
SUPABASE_STUDIO_HOST_PORT=8001
# OPENAI_API_KEY="sk-yourActualOpenAIapiKeyGoesHere"
ENVEXEOF
    cp "./.env.example" "./.env"
    _ks_log_info "Created n8n Hub docker-compose.yml and .env."
}
_ks_create_python_placeholders() {
    _ks_log_info "Creating n8n Hub Python service placeholders..."
    mkdir -p "./python_service/app"; mkdir -p "./python_service/tests"
    cat << 'PYMAINEOF' > "./python_service/app/main.py"
# PRF-SUPAGROK-PYSERVICEPLC-N8NTRANSLATOR-20250510
# UUID: pyservice-n8n-translator-main-uuid-v3; Timestamp: 2025-05-10T21:00:00Z
# Description: (supagrok_n8n_code_translator/python_service/app/main.py) Placeholder Python for n8n Hub.
# Version: 0.2.1; Author: SupagrokAgent/1.5; PRF-Codex-Version: 1.7
import json, logging, sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'); logger = logging.getLogger(__name__)
def process_code_snippet_example(d):
    logger.info(f"Processing: {json.dumps(d, indent=2)}"); o=d.get("code","");
    r=f"# PRF-HDR\n{o}\n# END"; deps=["pandas" if "pandas" in o else None, "numpy" if "numpy" in o else None]
    return {"original_code":o,"refined_code":r,"identified_dependencies":list(filter(None,deps)),"status":"success","message":"Simulated refinement."}
if __name__ == "__main__":
    if len(sys.argv) > 1: # Check if it's sys.argv[1])
        try: print(json.dumps(process_code_snippet_example(json.loads(sys.argv[1]))))
        except Exception as e: print(json.dumps({"status":"error","message":str(e)})); sys.exit(1)
    else: logger.info("Test run: process_code_snippet_example"); print(json.dumps(process_code_snippet_example({"code":"import pandas as pd\nprint('hi')"}), indent=2))
PYMAINEOF
    cat << 'PYREQSEOF' > "./python_service/requirements.txt"
# PRF-SUPAGROK-PYREQS-N8NTRANSLATOR-20250510
# UUID: pyreqs-n8n-translator-uuid-20250510-001; Timestamp: 2025-05-10T21:00:00Z
# Description: (supagrok_n8n_code_translator/python_service/requirements.txt) Python deps for n8n Hub service.
# Version: 1.0.1; Author: SupagrokAgent/1.5; PRF-Codex-Version: 1.7
python-dotenv>=1.0.0
PYREQSEOF
    cat << 'PYDOCKERFILEEOF' > "./python_service/Dockerfile"
# PRF-SUPAGROK-PYDOCKERFILE-N8NTRANSLATOR-20250510
# UUID: pydockerfile-n8n-translator-uuid-20250510-001; Timestamp: 2025-05-10T21:00:00Z
# Description: (supagrok_n8n_code_translator/python_service/Dockerfile) Dockerfile for n8n Hub Python service.
# Version: 1.0.1; Author: SupagrokAgent/1.5; PRF-Codex-Version: 1.7
FROM python:3.11-slim-bullseye; WORKDIR /app; COPY requirements.txt .; RUN pip install --no-cache-dir -r requirements.txt; COPY ./app /app
CMD ["python", "main.py", "{\"code\": \"print(\"Hello from Dockerized Python service!\")\"}"]
PYDOCKERFILEEOF
    _ks_log_info "Created n8n Hub Python service placeholders."
}
_ks_create_react_frontend() {
    _ks_log_info "Creating n8n Hub React frontend placeholders..."
    mkdir -p "./frontend/public"; mkdir -p "./frontend/src/components/common"; mkdir -p "./frontend/src/components/dashboard"; mkdir -p "./frontend/src/components/submission"; mkdir -p "./frontend/src/components/viewer"; mkdir -p "./frontend/src/hooks"; mkdir -p "./frontend/src/services"; mkdir -p "./frontend/src/contexts"; mkdir -p "./frontend/src/assets/styles"; mkdir -p "./frontend/src/assets/images"
    cat << 'PKGJSONEOF' > "./frontend/package.json"
{"name":"supagrok-code-translator-ui","private":true,"version":"0.1.0","type":"module","scripts":{"dev":"vite","build":"vite build","lint":"eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0","preview":"vite preview"},"dependencies":{"react":"^18.2.0","react-dom":"^18.2.0","react-router-dom":"^6.15.0"},"devDependencies":{"@types/react":"^18.2.15","@types/react-dom":"^18.2.7","@vitejs/plugin-react":"^4.0.3","eslint":"^8.45.0","eslint-plugin-react":"^7.32.2","eslint-plugin-react-hooks":"^4.6.0","eslint-plugin-react-refresh":"^0.4.3","vite":"^4.4.5"}}
PKGJSONEOF
    cat << 'VITEEOF' > "./frontend/vite.config.js"
import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react';
export default defineConfig({ plugins: [react()], server: { port: 3000, strictPort: true }});
VITEEOF
    cat << 'IDXHTMLEOF' > "./frontend/index.html"
<!doctype html><html lang="en"><head><meta charset="UTF-8" /><link rel="icon" type="image/svg+xml" href="/supagrok_icon.svg" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>Supagrok Code Hub</title></head><body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body></html>
IDXHTMLEOF
    echo '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">💡</text></svg>' > "./frontend/public/supagrok_icon.svg"
    cat << 'MAINJSXEOF' > "./frontend/src/main.jsx"
import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App.jsx'; import './assets/styles/global.css';
ReactDOM.createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>,);
MAINJSXEOF
    _ks_current_year_react=$(date +'%Y')
    cat << EOF > "./frontend/src/App.jsx"
import React from 'react'; import { BrowserRouter as R, Routes, Route } from 'react-router-dom'; import './App.css'; 
import Dash from './components/dashboard/DashboardPage'; import Sub from './components/submission/SubmissionPage';
import View from './components/viewer/ScriptViewerPage'; import Head from './components/common/Header'; import Foot from './components/common/Footer';
function App() { return (<R><div className="app-container"><Head /><main className="main-content"><Routes><Route path="/" element={<Dash />} /><Route path="/submit" element={<Sub />} /><Route path="/script/:id" element={<View />} /></Routes></main><Foot companyName="Supagrok Systems" year="${_ks_current_year_react}" /></div></R>); } export default App;
EOF
    cat << 'GLOBALCSSEOF' > "./frontend/src/assets/styles/global.css"
/* PRF-SUPAGROK-CSSGLOBAL-N8NTRANSLATOR-20250510 */ body { margin:0; font-family:sans-serif; background-color:#f0f2f5; color:#333; line-height:1.6; } .app-container { display:flex; flex-direction:column; min-height:100vh; } .main-content { flex-grow:1; padding:20px; max-width:1200px; margin:0 auto; width:100%; box-sizing:border-box; } button, input[type="submit"] { background-color:#007bff; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-size:1rem; transition:background-color 0.2s ease-in-out; } button:hover, input[type="submit"]:hover { background-color:#0056b3; } input[type="text"], textarea, select { padding:10px; border:1px solid #ccc; border-radius:5px; font-size:1rem; width:calc(100% - 22px); margin-bottom:10px; }
GLOBALCSSEOF
    echo "/* PRF-SUPAGROK-CSSAPP-N8NTRANSLATOR-20250510 */" > "./frontend/src/App.css"
    cat << 'HEADJSXEOF' > "./frontend/src/components/common/Header.jsx"
import React from 'react'; import { Link } from 'react-router-dom'; import './Header.css';
const Header = () => (<header className="app-header"><div className="logo-container"><span className="logo-text">💡 Supagrok Hub</span></div><nav className="main-nav"><Link to="/">Dashboard</Link><Link to="/submit">Submit</Link></nav></header>); export default Header;
HEADJSXEOF
    echo ".app-header { background-color:#2c3e50; padding:15px 30px; color:white; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 4px rgba(0,0,0,0.1); } .logo-container .logo-text { font-size:1.5rem; font-weight:bold; } .main-nav a { color:white; margin-left:20px; text-decoration:none; font-size:1rem; } .main-nav a:hover { text-decoration:underline; }" > "./frontend/src/components/common/Header.css"
    cat << 'FOOTJSXEOF' > "./frontend/src/components/common/Footer.jsx"
import React from 'react'; import './Footer.css';
const Footer = ({ companyName, year }) => (<footer className="app-footer"><p>&copy; {year} {companyName}.</p></footer>); export default Footer;
FOOTJSXEOF
    echo ".app-footer { text-align:center; padding:20px; background-color:#ecf0f1; color:#7f8c8d; font-size:0.9em; border-top:1px solid #dcdcdc; }" > "./frontend/src/components/common/Footer.css"
    echo "import React from 'react'; const D = () => <h2>Dashboard</h2>; export default D;" > "./frontend/src/components/dashboard/DashboardPage.jsx"
    echo "import React from 'react'; const S = () => <h2>Submit Code</h2>; export default S;" > "./frontend/src/components/submission/SubmissionPage.jsx"
    echo "import React from 'react'; import { useParams } from 'react-router-dom'; const V = () => { const {id}=useParams(); return <h2>Script ID: {id}</h2>; }; export default V;" > "./frontend/src/components/viewer/ScriptViewerPage.jsx"
    _ks_log_info "Created n8n Hub React frontend placeholders."
}
_ks_create_readme() {
    _ks_log_info "Creating n8n Hub README.md..."
    cat << 'READMEOF' > "./README.md"
# PRF-SUPAGROK-READMEN8N-N8NTRANSLATOR-20250510
# UUID: readme-n8n-translator-uuid-20250510-001; Timestamp: 2025-05-10T21:00:00Z
# Description: (supagrok_n8n_code_translator/README.md) README for n8n Hub.
# Version: 1.0.1; Author: SupagrokAgent/1.5; PRF-Codex-Version: 1.7
# Supagrok n8n Code Translator Project
Bootstrapped by \`kickstart_supagrok_n8n_translator.sh\`. Sets up n8n, Supabase, Python service placeholder, and React frontend.
## Project Structure
- \`docker-compose.yml\`: Services.
- \`.env\`, \`.env.example\`: Config.
- \`config/\`: Persistent data.
- \`python_service/\`: Python logic.
- \`frontend/\`: React UI.
## Prerequisites
- Docker & Docker Compose
- Node.js & npm/yarn
## Getting Started
1.  **Configure \`.env\`**: Copy \`.env.example\` to \`.env\` in project root and **update secrets**.
2.  **Start Services**: \`docker-compose up -d\`
3.  **n8n**: \`http://localhost:5678\` (default).
4.  **Supabase Studio**: Port in \`.env\` (default 8001).
5.  **Frontend Dev**: \`cd frontend && npm install && npm run dev\`.
Refer to Odoo ticket PRF-SUPAGROK-ODOOTICKET-N8N-TRANSLATOR-HUB-20250510.
READMEOF
    _ks_log_info "Created n8n Hub README.md."
}
_ks_main "$@"
KICKSTARTEOF
}


# --- Execute Main Orchestrator Function ---
main_orchestrator "$@"
