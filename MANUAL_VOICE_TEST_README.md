# Manual AI Voice Test

This document explains how to run the interactive AI-driven voice ordering test script, `manual_voice_test.py`.

This script simulates a conversation between a human agent (you) and an AI-powered customer named "Ravi" to test the complete voice interaction flow.

## Prerequisites

1.  **Python Environment**: Make sure you have Python 3.8+ installed.
2.  **Dependencies**: Install all required packages from `requirements.txt`.
    ```bash
    # Activate your virtual environment first
    source .venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt
    ```
3.  **Microphone**: A functional microphone must be connected and accessible to your system.
4.  **Ollama Server**: The Ollama service must be running locally with the `llama3.2` model available.

## How to Run the Test

1.  **Activate Environment**: Open your terminal and activate the Python virtual environment.
    ```bash
    source .venv/bin/activate
    ```

2.  **Run the Script**: Execute the `manual_voice_test.py` script.
    ```bash
    python manual_voice_test.py
    ```

3.  **Select Microphone**: The script will automatically try to find the default "MacBook Pro Microphone". If it can't, it will list all available microphones. Enter the number corresponding to the microphone you wish to use for speaking.

## The Test Flow

1.  **You are the Agent**: You will play the role of the "Pizza Company Agent".
2.  **Start the Conversation**: The script will prompt you to speak your opening line.
3.  **Listen for the Cue**: When you see the `🔴 Listening for Agent...` message, it's your turn to speak.
4.  **AI Responds**: The script will capture your voice, transcribe it, and send it to the AI customer, "Ravi." Ravi will then think and generate a spoken response.
5.  **Continue the Conversation**: The conversation will continue turn by turn. Your goal is to take Ravi's order and guide the conversation to a conclusion.

## How to End the Test Successfully

The test is designed to conclude when the order is finalized and ready for payment.

1.  **Confirm the Order**: Guide Ravi through the ordering process, confirming items as needed.
2.  **Initiate Payment Transfer**: Once the order is complete, you must state that you are transferring Ravi to the payment system. Use a phrase that includes the keywords **"transfer"** or **"payment"**.
    -   *Example: "Great, your order is confirmed. I will now **transfer** you to our secure app for **payment**."*
3.  **Automatic Termination**: The script will detect these keywords, Ravi will give a final acknowledgment (e.g., "Thank you."), and the test will automatically stop and display a success message.

You can also force-stop the script at any time by pressing `Ctrl+C` in the terminal.
