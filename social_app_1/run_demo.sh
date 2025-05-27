#!/bin/bash
# Social Security AI Workflow Demo Script
# This script automates running demos and tests for the enhanced AI workflow

set -e  # Exit on error

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${BOLD}=========================================================="
echo -e "  Social Security AI Workflow - Demonstration Script  "
echo -e "==========================================================${NC}"
echo

# Process command line arguments
GENERATE_DATA=false
RUN_DEMO=false
RUN_APP=false
DEBUG=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --generate-data)
      GENERATE_DATA=true
      shift
      ;;
    --run-demo)
      RUN_DEMO=true
      shift
      ;;
    --run-app)
      RUN_APP=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --all)
      GENERATE_DATA=true
      RUN_DEMO=true
      RUN_APP=true
      shift
      ;;
    --help)
      echo -e "${BOLD}Usage:${NC}"
      echo "  ./run_demo.sh [options]"
      echo
      echo -e "${BOLD}Options:${NC}"
      echo "  --generate-data  Generate synthetic test data"
      echo "  --run-demo       Run the demo workflow"
      echo "  --run-app        Run the Streamlit application"
      echo "  --debug          Enable debug logging"
      echo "  --all            Run all steps (generate data, demo, and app)"
      echo "  --help           Display this help message"
      echo
      exit 0
      ;;
    *)
      echo -e "${RED}Error: Unknown option $1${NC}"
      echo "Use --help to see available options"
      exit 1
      ;;
  esac
done

# If no arguments provided, show help
if [[ "$GENERATE_DATA" == "false" && "$RUN_DEMO" == "false" && "$RUN_APP" == "false" ]]; then
  echo -e "${YELLOW}No options specified. Use --help to see available options.${NC}"
  echo
  echo -e "${BOLD}Running interactive menu:${NC}"
  
  echo "What would you like to do?"
  echo "1) Generate synthetic test data"
  echo "2) Run the demo workflow"
  echo "3) Launch the Streamlit application"
  echo "4) Run all of the above"
  echo "5) Exit"
  read -p "Enter your choice (1-5): " choice
  
  case $choice in
    1)
      GENERATE_DATA=true
      ;;
    2)
      RUN_DEMO=true
      ;;
    3)
      RUN_APP=true
      ;;
    4)
      GENERATE_DATA=true
      RUN_DEMO=true
      RUN_APP=true
      ;;
    5)
      echo "Exiting."
      exit 0
      ;;
    *)
      echo -e "${RED}Invalid choice. Exiting.${NC}"
      exit 1
      ;;
  esac
fi

# Check if virtual environment exists, and activate it
if [ -d ".venv" ]; then
  echo -e "${GREEN}Activating virtual environment...${NC}"
  source .venv/bin/activate
else
  echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
  python3 -m venv .venv
  source .venv/bin/activate
  echo -e "${GREEN}Installing dependencies...${NC}"
  pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}Creating default .env file...${NC}"
  cat > .env << EOL
# Database configuration
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=social

# LLM configuration
OLLAMA_BASE_URL=http://localhost:11434

# Observability configuration
LANGSMITH_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
EOL
  echo -e "${GREEN}Created default .env file. Please update with your credentials.${NC}"
fi

# Generate synthetic data if requested
if [[ "$GENERATE_DATA" == "true" ]]; then
  echo -e "\n${BOLD}Generating synthetic test data...${NC}"
  python3 -m data.synthetic.generate_test_data
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Synthetic data generated successfully!${NC}"
  else
    echo -e "${RED}Error generating synthetic data.${NC}"
    exit 1
  fi
fi

# Run the demo workflow if requested
if [[ "$RUN_DEMO" == "true" ]]; then
  echo -e "\n${BOLD}Running the demo workflow...${NC}"
  
  # Additional arguments if debug is enabled
  DEBUG_ARGS=""
  if [[ "$DEBUG" == "true" ]]; then
    DEBUG_ARGS="--debug"
  fi
  
  python3 demo_workflow.py $DEBUG_ARGS
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Demo workflow completed successfully!${NC}"
  else
    echo -e "${RED}Error running demo workflow.${NC}"
    exit 1
  fi
fi

# Run the Streamlit app if requested
if [[ "$RUN_APP" == "true" ]]; then
  echo -e "\n${BOLD}Launching the Streamlit application...${NC}"
  
  # Check if we can find streamlit in the user's Python directory
  STREAMLIT_PATH="$HOME/Library/Python/3.9/bin/streamlit"
  
  if [ -f "$STREAMLIT_PATH" ]; then
    echo -e "${GREEN}Found Streamlit at: $STREAMLIT_PATH${NC}"
    $STREAMLIT_PATH run enhanced_app.py
  else
    echo -e "${YELLOW}Streamlit not found at expected location.${NC}"
    echo -e "${YELLOW}Trying alternative approaches...${NC}"
    
    # Try with python3 -m streamlit
    echo -e "${GREEN}Running with python3 -m streamlit...${NC}"
    python3 -m streamlit run enhanced_app.py
  fi
fi

echo -e "\n${GREEN}All tasks completed successfully!${NC}"
