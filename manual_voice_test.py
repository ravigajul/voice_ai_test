
#source /Users/ravigajul/Documents/pizza-voice-test/.venv/bin/activate && python3 /Users/ravigajul/Documents/pizza-voice-test/manual_voice_test.py
"""
Interactive AI-driven Voice Ordering Test

This script simulates a conversation between an AI customer ("Ravi") and a human
acting as a pizza ordering agent.

Instructions:
1. Run this script: `python manual_voice_test.py`
2. Select the microphone you will use to speak as the agent.
3. The AI customer, "Ravi," will start the conversation.
4. When you see "🔴 Listening for Agent...", speak your response as the
   Papa John's agent.
5. The script will transcribe your response, and Ravi will reply.
6. The conversation continues until the order is complete or someone says "exit".
"""

import speech_recognition as sr
import sys
from src.ollama_client import OllamaClient
from src.voice_ai import speak_sync

RAVI_PERSONA = """
You are Ravi, a busy customer calling Papa John's to order pizza.

**Your Goal:**
1.  Order pizza and any side items for your family.
2.  Confirm the final order details with the agent.
3.  Wait for the agent to ask you to finalize the order for payment.
4.  When the agent asks for final confirmation, you should agree (e.g., "Yes, that's correct, please proceed.").
5.  The conversation concludes when the agent confirms they are transferring you to the payment system. Your final response should be a simple acknowledgment like "Thank you." or "Great."

**Your Personality:**
- You are direct and a little impatient, but not rude.
- You want to be efficient.

**Rules of Conversation:**
- **DO NOT** repeat the entire order back to the agent unless they ask you to. A simple "yes" or "that's correct" is enough for confirmation.
- **CRITICAL:** Your response must ONLY be Ravi's dialogue. Do NOT include any explanations, parenthetical thoughts, or out-of-character text.
- Once the agent says they are transferring you for payment, the conversation is over from your side. Just give a brief, final acknowledgment.
"""


def select_microphone():
    """Lists available microphones and prompts the user to select one."""
    mics = sr.Microphone.list_microphone_names()
    if not mics:
        print("❌ No microphones found. Please ensure a microphone is connected.")
        sys.exit(1)

    print("🎤 Available Microphones:")
    for i, name in enumerate(mics):
        print(f"   {i}: {name}")

    while True:
        try:
            mic_index = int(
                input(
                    "\nSelect the microphone for the AGENT's voice (enter the number): "
                )
            )
            if 0 <= mic_index < len(mics):
                print(f"✅ Using microphone: {mics[mic_index]}\n")
                return mic_index
            else:
                print("Invalid number. Please try again.")
        except (ValueError, IndexError):
            print("Invalid input. Please enter a number from the list.")


def main():
    """Main function to run the interactive voice ordering session."""
    mic_index = None
    try:
        # Try to find and set the default microphone
        mics = sr.Microphone.list_microphone_names()
        default_mic_name = "MacBook Pro Microphone"

        for i, name in enumerate(mics):
            if default_mic_name in name:
                mic_index = i
                print(f"✅ Default microphone found: {name}\n")
                break

        # If default not found, ask the user
        if mic_index is None:
            print("⚠️  Default microphone not found.")
            mic_index = select_microphone()

        recognizer = sr.Recognizer()
        ollama = OllamaClient()

        print("You are the Papa John's Agent. Speak your opening line.")
        print("-" * 60)

        conversation_history = []
        turn = 1

        while True:
            print(f"--- Turn {turn} ---")

            try:
                # 1. Listen for the Agent's (Human) response
                with sr.Microphone(device_index=mic_index) as source:
                    recognizer.dynamic_energy_threshold = True
                    recognizer.pause_threshold = 1.8  # Give human more time to pause

                    print("\n   🔴 Listening for Agent...")
                    audio = recognizer.listen(source, timeout=45, phrase_time_limit=30)

                print("   🔄 Transcribing agent's speech...")
                agent_speech = recognizer.recognize_whisper(audio, model="tiny.en")
                print(f'   👨‍💼 Agent (You): "{agent_speech}"')
                conversation_history.append(f"Agent: {agent_speech}")

                if "exit" in agent_speech.lower() or "goodbye" in agent_speech.lower():
                    print("\n🛑 Agent ended the session.")
                    break

                # Check for termination condition based on agent's speech
                agent_lower = agent_speech.lower()
                if any(keyword in agent_lower for keyword in ["transfer", "payment"]):
                    print("\n✅ Agent initiated payment transfer. Ending conversation.")
                    # Also get Ravi's final "Thank you"
                    speak_sync("Thank you.")
                    break

                # 2. Get AI response
                print("   🤖 Ravi is thinking...")
                prompt = f"Conversation History:\n" + "\n".join(conversation_history)
                prompt += "\n\nYou are Ravi. What do you say next?"

                ravi_response = ollama.generate(prompt, system=RAVI_PERSONA)

                # 3. Ravi (AI) speaks
                print(f'   👤 Ravi (AI): "{ravi_response}"')
                speak_sync(ravi_response)
                conversation_history.append(f"Ravi: {ravi_response}")

                # 4. Check if Ravi is ending the conversation
                end_phrases = ["goodbye", "that's all", "thanks, bye"]
                if any(phrase in ravi_response.lower() for phrase in end_phrases):
                    print("\n✅ Ravi has ended the conversation. Test complete.")
                    break

            except sr.UnknownValueError:
                print("   ⚠️  Could not understand audio. Please try again.")
                continue
            except sr.RequestError as e:
                print(f"   Could not request results; {e}")
                continue

            turn += 1
            print("-" * 60)

    except KeyboardInterrupt:
        print("\n🛑 Session interrupted by user. Exiting.")
    except Exception as e:
        print(f"\n❌ A critical error occurred: {e}")


if __name__ == "__main__":
    main()
