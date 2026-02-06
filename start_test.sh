#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Activate Virtual Environment ---
echo "Activating Python virtual environment..."
source .venv/bin/activate

# --- Install Dependencies ---
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Function to check if a process is running by name
is_process_running() {
  pgrep -f "$1" > /dev/null
}


# --- Check and Start Appium ---
if is_process_running "appium"; then
  echo "Appium is already running."
else
  echo "Starting Appium..."
  appium &
  # Wait for Appium to initialize
  sleep 10
  echo "Appium started."
fi

# --- Check and Start Ollama ---
if is_process_running "ollama"; then
  echo "Ollama is already running."
else
  echo "Starting Ollama..."
  ollama serve &
  # Wait for Ollama to initialize
  sleep 10
  echo "Ollama started."
fi

# --- Navigate to the Voice Agent Screen ---
echo "Running navigation script..."
python3 navigate_to_voice_agent.py

# --- Run the Manual Voice Test ---
echo "Starting the manual voice test..."
python3 manual_voice_test.py

echo "Test script finished."
