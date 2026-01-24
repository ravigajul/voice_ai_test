#!/usr/bin/env python3
"""
Customer Agent - Simulates a busy parent ordering pizza
Interacts with the VoiceAgent to test ordering flow
"""
import asyncio
from typing import Optional
from src.ollama_client import OllamaClient
from src.voice_ai import VoiceAI


class CustomerAgent:
    """Simulates a customer (busy parent) ordering pizza"""

    def __init__(self, ollama_model: str = "llama3.2"):
        """
        Initialize customer agent

        Args:
            ollama_model: Ollama model to use for generating customer responses
        """
        self.ollama = OllamaClient(model=ollama_model)
        self.voice_ai = VoiceAI(voice="en-US-AmberNeural")  # Different voice from agent
        self.conversation_history = []
        self.interaction_count = 0

        self.system_prompt = """You are a busy parent trying to order pizza for your family.
        
Character traits:
- Impatient but polite
- Has specific preferences (kids don't like certain toppings)
- Wants it quick and convenient
- May ask about pricing
- Looking for a good deal if possible

Your goals in this order (prioritize):
1. Confirm the order size and type
2. Add your customizations (cheese, toppings)
3. Handle any side orders or drinks
4. Get price confirmation
5. Complete the order

Keep responses natural and conversational. Be realistic - ask clarifying questions if needed.
Respond with just what you would say (no "Me:" prefix)."""

        if not self.ollama.is_available():
            raise RuntimeError("Ollama server not available")

        print("✅ Customer Agent initialized")

    async def generate_response(self, agent_message: str) -> Optional[str]:
        """
        Generate customer response to agent message

        Args:
            agent_message: The agent's message to respond to

        Returns:
            Customer's response text
        """
        # Add agent message to history
        self.conversation_history.append({"role": "agent", "content": agent_message})

        # Build conversation context
        messages = "\n".join(
            [
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in self.conversation_history[-6:]  # Keep last 6 messages
            ]
        )

        prompt = f"""Conversation so far:
{messages}

Agent just said: "{agent_message}"

Respond as a busy parent customer. Keep it brief and natural (1-2 sentences max).
Focus on ordering a pizza. Don't be overly polite, be direct."""

        response = self.ollama.generate(prompt, system=self.system_prompt)

        if response:
            # Clean up response
            response = response.strip()
            # Remove any role prefixes if they exist
            for prefix in ["Customer:", "Me:", "Customer Agent:", "User:"]:
                if response.startswith(prefix):
                    response = response[len(prefix) :].strip()

            self.conversation_history.append({"role": "customer", "content": response})

            return response

        return None

    async def speak(self, text: str) -> None:
        """Generate and play customer speech"""
        print(f"\n👤 Customer: '{text}'")
        try:
            await self.voice_ai.speak(text, filename="customer_utterance")
        except Exception as e:
            print(f"   ⚠️  TTS error (continuing): {str(e)[:50]}")

    async def get_opening_statement(self) -> str:
        """Get initial customer statement to start interaction"""
        prompt = """Generate an opening statement as a busy parent ordering pizza.
        
Be direct and show you're busy but polite. Keep it short (1 sentence).
Don't include any preamble or explanation, just the statement."""

        response = self.ollama.generate(prompt, system=self.system_prompt)

        if response:
            response = response.strip()
            # Remove quotes if present
            response = response.strip("\"'")
            self.conversation_history.append({"role": "customer", "content": response})
            return response

        return "Hi, I'd like to order a pizza please."

    def get_conversation_length(self) -> int:
        """Get number of conversation turns"""
        return len([m for m in self.conversation_history if m["role"] == "customer"])
