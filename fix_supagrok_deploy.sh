#!/usr/bin/env bash
# PRF-compliant one-shot fix for supagrok_deploy.sh variable expansion

set -euo pipefail

DEPLOY_SCRIPT="supagrok_deploy.sh"
TMP_SCRIPT="${DEPLOY_SCRIPT}.tmp"

awk '
/ssh -o BatchMode=yes/ {
    print $0
    in_heredoc=1
    next
}
in_heredoc && /chmod \+x \\\${SETUP_SCRIPT}/ {
    sub(/chmod \+x \\\${SETUP_SCRIPT}/, "chmod +x ${SETUP_SCRIPT}")
    print
    next
}
in_heredoc && /\.\/\\\${SETUP_SCRIPT}/ {
    sub(/\.\/\\\${SETUP_SCRIPT}/, "./${SETUP_SCRIPT}")
    print
    in_heredoc=0
    next
}
{ print }
' "$DEPLOY_SCRIPT" > "$TMP_SCRIPT"

mv "$TMP_SCRIPT" "$DEPLOY_SCRIPT"
chmod +x "$DEPLOY_SCRIPT"

echo "✅ supagrok_deploy.sh has been automatically corrected for variable expansion."