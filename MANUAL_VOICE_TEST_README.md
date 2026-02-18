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

2.  **Run the Script**: You can run the test in three ways:

    ### Option A: Default Persona

    Uses the standard "busy customer" persona.

    ```bash
    python manual_voice_test.py
    ```

    ### Option B: Pre-built Persona File

    Choose from available personas in the `personas/` directory.

    ```bash
    # List all available personas
    python manual_voice_test.py --list-personas

    # Run with a specific persona
    python manual_voice_test.py --persona rushed
    python manual_voice_test.py --persona indecisive
    python manual_voice_test.py --persona large_order
    ```

    **Available personas:**

    | Persona      | Description                                                           |
    | ------------ | --------------------------------------------------------------------- |
    | `default`    | Clear, concise customer ordering pepperoni + veggie + garlic knots    |
    | `rushed`     | Impatient customer who gives the entire order upfront in minimal words |
    | `indecisive` | Hesitant customer who asks about specials and changes their mind      |
    | `large_order` | Friendly customer placing a big party order across multiple categories |

    ### Option C: Dynamic Scenario (AI-generated persona)

    Describe any test scenario in plain English and a persona will be generated at runtime.

    ```bash
    # Customer with hearing difficulty
    python manual_voice_test.py --scenario "customer who is hard of hearing and keeps asking the agent to repeat"

    # Angry customer
    python manual_voice_test.py --scenario "angry customer who received the wrong order last time and wants a discount"

    # Confused elderly customer
    python manual_voice_test.py --scenario "elderly customer who is confused about the menu and needs help choosing"

    # Customer who changes delivery to pickup
    python manual_voice_test.py --scenario "customer who starts ordering for delivery but then changes to pickup halfway through"

    # Non-native English speaker
    python manual_voice_test.py --scenario "customer whose first language is not English and uses simple vocabulary"
    ```
    The generated persona will be printed to the console before the conversation starts so you can review it.

3.  **Select Microphone**: The script will automatically search for a default microphone.
    - The default search term is `"MacBook Pro Microphone"`.
    - You can override this with the `--mic` flag. For example: `python manual_voice_test.py --mic "My Headset"`
    - If the specified microphone isn't found, the script will list all available devices and prompt you to select one by number.

## Adding a New Persona

To create a reusable persona, add a `.txt` file to the `personas/` directory. Use `personas/default.txt` as a template. The filename (without `.txt`) becomes the persona name you pass to `--persona`.

## The Test Flow

1.  **You are the Agent**: You will play the role of the "Pizza Company Agent".
2.  **Start the Conversation**: The script will prompt you to speak your opening line.
3.  **Listen for the Cue**: When you see the `🔴 Listening for Agent...` message, it's your turn to speak.
4.  **AI Responds**: The script will capture your voice, transcribe it, and send it to the AI customer, "Ravi." Ravi will then think and generate a spoken response.
5.  **Continue the Conversation**: The conversation will continue turn by turn. Your goal is to take Ravi's order and guide the conversation to a conclusion.

## Conversation Logs

For quality assurance and review, a full transcript of every test run is automatically saved.

-   **Location**: A new `logs/` directory is created in the project root.
-   **Filename**: Each log is a `.txt` file named with the exact date and time of the test run (e.g., `test_run_20240521_153000.txt`).
-   **Content**: The log contains the persona used, the timestamp, and the full back-and-forth dialogue between the agent and Ravi.

## How to End the Test Successfully

The test is designed to conclude when the order is finalized and ready for payment.

1.  **Confirm the Order**: Guide Ravi through the ordering process, confirming items as needed.
2.  **Initiate Payment Transfer**: Once the order is complete, you must state that you are transferring Ravi to the payment system. Use a phrase that includes the keywords **"transfer"** or **"payment"**.
    -   *Example: "Great, your order is confirmed. I will now **transfer** you to our secure app for **payment**."*
3.  **Automatic Termination**: The script will detect these keywords, Ravi will give a final acknowledgment (e.g., "Thank you."), and the test will automatically stop and display a success message.

You can also force-stop the script at any time by pressing `Ctrl+C` in the terminal.
