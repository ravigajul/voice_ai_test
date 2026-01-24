#!/usr/bin/env python3
"""
Voice Agent - Integrates Ollama LLM, Speech Recognition, and TTS
Handles bidirectional voice interaction with the pizza ordering app
"""
import speech_recognition as sr
import asyncio
import json
from typing import Optional, Dict, Tuple
from src.ollama_client import OllamaClient
from src.voice_ai import VoiceAI
from src.appium_driver import AppiumDriver


class VoiceAgent:
    """Voice-enabled AI agent for app interaction"""

    def __init__(
        self,
        driver: AppiumDriver,
        ollama_model: str = "llama3.2",
        voice: str = "en-US-JennyNeural",
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize the voice agent

        Args:
            driver: AppiumDriver instance for app interaction
            ollama_model: Ollama model to use
            voice: TTS voice name
            system_prompt: Custom system prompt for the agent
        """
        self.driver = driver
        self.ollama = OllamaClient(model=ollama_model)
        self.voice_ai = VoiceAI(voice=voice)
        self.recognizer = sr.Recognizer()

        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.conversation_history = []

        # Check Ollama availability
        if not self.ollama.is_available():
            raise RuntimeError(
                "❌ Ollama server not available at http://localhost:11434\n"
                "   Please start Ollama first: ollama serve"
            )

        print("✅ Voice Agent initialized successfully")

    def _get_default_system_prompt(self) -> str:
        """Default system prompt for pizza ordering agent"""
        return """You are a helpful pizza ordering assistant for Papa John's Pizza.
        
Your capabilities:
- Help users order pizza and customize their preferences
- Answer questions about menu items, pricing, and specials
- Guide users through the ordering process
- Handle delivery preferences, payment, and other order details

Keep responses concise and natural, as if speaking to a customer.
Respond with clear, actionable information.
Always be helpful and professional."""

    def listen(self, timeout: float = 10) -> Optional[str]:
        """
        Listen for voice input from user

        Args:
            timeout: Timeout in seconds for listening

        Returns:
            Transcribed text or None if failed
        """
        try:
            print("\n🎤 Listening...")
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=15
                )

            print("   Processing audio...")
            text = self.recognizer.recognize_google(audio)
            print(f"   👤 User said: '{text}'")
            return text

        except sr.UnknownValueError:
            print("   ⚠️  Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"   ❌ Speech recognition error: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    async def speak(self, text: str, prefix: str = "🤖 Agent") -> None:
        """
        Generate and play voice response

        Args:
            text: Text to speak
            prefix: Prefix for console output
        """
        print(f"\n{prefix} says: '{text}'")
        try:
            await self.voice_ai.speak(text)
        except Exception as e:
            print(f"   ⚠️  TTS error (continuing): {str(e)[:50]}")

    def _get_app_context(self) -> str:
        """Get current app state for context"""
        try:
            visible_texts = self.driver.get_visible_text_elements()
            activity = self.driver.driver.current_activity

            context = f"""Current App State:
- Activity: {activity}
- Visible UI elements: {', '.join(visible_texts[:10]) if visible_texts else 'None'}
- Screen is responsive: {'Yes' if visible_texts else 'No'}

Based on this context, respond to the user's request."""

            return context
        except:
            return "Current app state is unknown. Continue assisting the user."

    async def process_voice_input(self, user_input: str) -> Optional[str]:
        """
        Process voice input through Ollama and generate response

        Args:
            user_input: User's voice command

        Returns:
            Agent's response text
        """
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})

        # Build conversation context
        messages = "\n".join(
            [
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in self.conversation_history[-5:]  # Keep last 5 messages
            ]
        )

        app_context = self._get_app_context()

        prompt = f"""{app_context}

Conversation history:
{messages}

Respond naturally and helpfully to the user's latest request."""

        print("\n   🤔 Thinking...")
        response = self.ollama.generate(prompt, system=self.system_prompt)

        if response:
            self.conversation_history.append({"role": "agent", "content": response})
            return response
        else:
            return "I'm sorry, I encountered an error processing your request."

    async def interactive_session(self, duration_minutes: int = 10) -> None:
        """
        Start an interactive voice session

        Args:
            duration_minutes: How long to keep session active
        """
        import time

        print("\n" + "=" * 60)
        print("🎤 VOICE AGENT INTERACTIVE SESSION")
        print("=" * 60)
        print(f"\nSession Duration: {duration_minutes} minutes")
        print("Commands:")
        print("  - Say anything to interact")
        print("  - Say 'help' for available options")
        print("  - Say 'exit' to end session")
        print("\n" + "-" * 60)

        start_time = time.time()
        session_timeout = duration_minutes * 60
        turn_count = 0

        while time.time() - start_time < session_timeout:
            turn_count += 1
            print(f"\n[Turn {turn_count}]")

            # Listen for user input
            user_input = self.listen(timeout=10)

            if not user_input:
                print("   Waiting for input...")
                continue

            # Check for exit command
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("\n👋 Ending session...")
                await self.speak(
                    "Thank you for using Papa John's Voice Ordering. Goodbye!"
                )
                break

            # Check for help command
            if user_input.lower() in ["help", "what can you do"]:
                help_text = """I can help you with:
- Ordering pizzas
- Customizing your toppings and crust
- Checking prices and menu items
- Handling delivery and pickup options
- Processing your payment
- Answering questions about Papa John's"""
                await self.speak(help_text)
                continue

            # Process through voice agent
            response = await self.process_voice_input(user_input)

            if response:
                await self.speak(response)
            else:
                await self.speak("I didn't catch that. Can you please repeat?")

        print("\n" + "=" * 60)
        print(f"✅ SESSION ENDED - {turn_count} turns completed")
        print("=" * 60)

    def run_session(self, duration_minutes: int = 10) -> None:
        """Synchronous wrapper for interactive session"""
        asyncio.run(self.interactive_session(duration_minutes))


if __name__ == "__main__":
    from src.appium_driver import AppiumDriver

    # Initialize driver and agent
    driver = AppiumDriver("config/appium_config.yaml")
    driver.start()

    try:
        agent = VoiceAgent(driver)
        agent.run_session(duration_minutes=10)
    finally:
        driver.stop()
