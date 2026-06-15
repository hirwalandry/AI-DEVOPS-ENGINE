#!/bin/bash

API_GATEWAY_URL="${PATCHBOT_API_URL:-http://localhost}"
CONFIG_FILE=".patchbot.env"

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_CYAN}Initializing Autonomous AI Patch-Bot Engine client...${COLOR_RESET}"

if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

if [ -z "$PATCHBOT_API_KEY" ]; then
    echo -e "${COLOR_RED}Configuration Error: PATCHBOT_API_KEY variable is empty or unassigned.${COLOR_RESET}"
    echo -e "Please create a '${CONFIG_FILE}' file locally or export the variable into your environment:"
    echo -e "export PATCHBOT_API_KEY=\"sk_live_...\""
    exit 1
fi

TARGET_FILE=$1
BUG_DESCRIPTION=$2

if [ -z "$TARGET_FILE" ] || [ -z "$BUG_DESCRIPTION" ]; then
    echo -e "${COLOR_YELLOW}Usage Missing Arguments:${COLOR_RESET}"
    echo -e "  ./infra/patch-bot.sh <target_file_path> \"<detailed_bug_description>\""
    echo -e "Example:"
    echo -e "  ./infra/patch-bot.sh src/auth.py \"Fix off-by-one error handling array tokens.\""
    exit 1
fi

if [ ! -f "$TARGET_FILE" ]; then
    echo -e "${COLOR_RED}Error: Targeted source file context not found locally: $TARGET_FILE${COLOR_RESET}"
    exit 1
fi

FILE_EXTENSION="${TARGET_FILE##*.}"
TARGET_LANGUAGE=""

case "$FILE_EXTENSION" in
    py)
        TARGET_LANGUAGE="python"
        ;;
    js|jsx|ts|tsx)
        TARGET_LANGUAGE="javascript"
        ;;
    *)
        echo -e "${COLOR_RED}Error: Unsupported system file type detected (.${FILE_EXTENSION}). Only Python and JavaScript assets are permitted in this cycle.${COLOR_RESET}"
        exit 1
        ;;
esac

echo -e "Targeting File: ${COLOR_YELLOW}${TARGET_FILE}${COLOR_RESET} [Language Strategy Matrix: ${COLOR_GREEN}${TARGET_LANGUAGE}${COLOR_RESET}]"
echo -e "Bug Matrix: \"${BUG_DESCRIPTION}\""

BUGGY_FILE_CONTENT=$(cat "$TARGET_FILE")
PROJECT_ID="cli_run_$(date +%s)_$((RANDOM % 1000))"

echo -e "${COLOR_CYAN}Dispatching code safely to cloud parsing nodes...${COLOR_RESET}"

PAYLOAD=$(cat <<EOF
{
    "project_id": "${PROJECT_ID}",
    "target_language": "${TARGET_LANGUAGE}",
    "bug_description": $(echo "$BUG_DESCRIPTION" | jq -R .),
    "buggy_file_content": $(echo "$BUGGY_FILE_CONTENT" | jq -R -s .)
}
EOF
)

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_GATEWAY_URL/api/v1/cli/trigger-fix" \
    -H "Authorization: Bearer ${PATCHBOT_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

HTTP_BODY=$(echo "$RESPONSE" | sed '$d')
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 202 ]; then
    echo -e "${COLOR_GREEN}Success! Execution tasks assigned smoothly to backend processing pools.${COLOR_RESET}"
    echo -e "--------------------------------------------------------"
    echo "$HTTP_BODY" | jq -r '.message // "Tracking payload confirmed."'
    echo -e "--------------------------------------------------------"
    echo -e "Check your team's ${COLOR_CYAN}Slack Alerts Channel${COLOR_RESET} or your ${COLOR_CYAN}Django History Dashboard${COLOR_RESET} to view live container telemetry logs."
    exit 0
else
    echo -e "${COLOR_RED}Gateway Execution Interruption (Server Status: $HTTP_STATUS)${COLOR_RESET}"
    echo "$HTTP_BODY" | jq -r '.error // "An unexpected infrastructure processing rejection occurred."'
    exit 1
fi
