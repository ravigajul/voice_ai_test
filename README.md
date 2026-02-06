# AI-Powered Voice Ordering Automation Test

This project provides an end-to-end testing framework for a food ordering mobile application, combining traditional UI automation with AI-driven voice interaction.

The test launches the target application, navigates to the voice ordering screen, and then initiates a full, interactive conversation with an AI customer to place an order.

## Features

-   **UI Automation**: Uses `Appium` to navigate the Android application to the desired screen.
-   **Voice Interaction**: Simulates a complete customer conversation using:
    -   **Speech-to-Text**: `OpenAI Whisper` for accurately transcribing the agent's voice.
    -   **AI Customer**: `Ollama (llama3.2)` to generate realistic, persona-driven customer responses.
    -   **Text-to-Speech**: `EdgeTTS` for speaking the AI customer's dialogue.
-   **Configurable**: Easily configure Appium server details and application paths via `config/appium_config.yaml`.
-   **Manual Test Mode**: Includes a standalone script (`manual_voice_test.py`) for interactively testing and refining the voice conversation logic without running the full UI automation.

## Project Structure

```
.
├── config/
│   └── appium_config.yaml      # Appium server and capabilities configuration
├── src/
│   ├── appium_driver.py        # Handles Appium driver setup and teardown
│   ├── ollama_client.py        # Client for interacting with the Ollama LLM
│   └── voice_ai.py             # Manages Text-to-Speech and audio playback
├── navigate_to_voice_agent.py  # Main script to run the end-to-end test
├── manual_voice_test.py        # Standalone script for manual voice conversation testing
├── MANUAL_VOICE_TEST_README.md # Instructions for the manual test script
└── requirements.txt            # Python dependencies
```

## Prerequisites

1.  **Android Device/Emulator**: An active Android device (with USB debugging enabled) or a running Android emulator.
2.  **Appium Server**: An Appium 2.0 server must be running and accessible.
3.  **Ollama Service**: The [Ollama](https://ollama.com/) service must be running locally.
4.  **Ollama Model**: The `llama3.2` model must be pulled and available.
    ```bash
    ollama pull llama3.2
    ```
5.  **Python 3.8+**

## Setup and Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd pizza-voice-test
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Appium**
    -   Open `config/appium_config.yaml`.
    -   Update the `appium_server_url`.
    -   Modify the `capabilities` to match your target device and application (`appPackage`, `appActivity`, `platformVersion`, etc.).

## How to Run

### End-to-End Automated Test

This is the main test that combines UI navigation and voice interaction.

1.  Ensure your Appium server and Ollama service are running.
2.  Ensure your Android device/emulator is ready.
3.  Run the main script:
    ```bash
    python navigate_to_voice_agent.py
    ```
4.  The script will launch the app and navigate to the voice screen. Once there, the voice conversation will begin. You will act as the agent. Follow the prompts in the console.

### Manual Voice Conversation Test

Use this script to test only the voice interaction part of the flow.

-   For detailed instructions, please see [MANUAL_VOICE_TEST_README.md](MANUAL_VOICE_TEST_README.md).
-   To run the script:
    ```bash
    python manual_voice_test.py
    ```
