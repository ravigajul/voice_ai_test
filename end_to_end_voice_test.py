#!/usr/bin/env python3
"""
End-to-End Voice Ordering Test with AI Customer
Integrates: launch_and_invoke_voice.py + manual_voice_test.py + verify_order.py

Physical audio setup:
- Computer speakers → Phone microphone (Ravi's TTS reaches phone)
- Phone speaker → Computer microphone (App's voice reaches Ravi's STT)
"""

import argparse
import glob
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import speech_recognition as sr
from src.ollama_client import OllamaClient
from src.voice_ai import speak_sync

# Import navigation functions
from launch_and_invoke_voice import (
    launch_app,
    scroll_to_start_voice_order,
    click_start_voice_order,
    click_arrow_on_ready_screen,
    grant_microphone_permission,
    verify_voice_agent_active,
    get_voice_session_id,
)

# Import verification
from verify_order import verify_order

PERSONAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "personas")

PERSONA_GENERATOR_SYSTEM = """You are a test scenario designer for a pizza ordering voice AI system.
Given a user's test scenario description, generate a detailed customer persona prompt.
The persona is always named "Ravi" and is calling Papa John's to order pizza.

You MUST output ONLY the persona prompt text — no commentary, no markdown fences, no preamble.

Follow this exact structure:
1. Opening line describing who Ravi is and the scenario context
2. **Your Order:** — the specific items Ravi wants to order
3. **Conversation Flow:** — numbered steps for Greeting, Ordering, Time Confirmation, Order Review, Final Confirmation, and Handoff
4. **Personality:** — bullet points describing how Ravi behaves
5. **Rules:** — output rules (spoken dialogue only, concise, etc.)
6. **Example Responses:** — 4-6 short example lines Ravi might say"""


def load_persona(name):
    """Load persona text from personas/ directory."""
    filepath = os.path.join(PERSONAS_DIR, f"{name}.txt")
    if not os.path.isfile(filepath):
        filepath = os.path.join(PERSONAS_DIR, "default.txt")
    with open(filepath, "r") as f:
        return f.read()


def generate_persona_from_scenario(scenario, ollama):
    """Use Ollama to generate a persona prompt from a free-text scenario description."""
    example_persona = load_persona("default")
    prompt = f"""Here is an example persona for reference:

---
{example_persona}
---

Now generate a NEW persona for this test scenario:
"{scenario}"

Output only the persona text, matching the structure of the example above."""

    print("🧠 Generating persona from scenario description...")
    try:
        persona = ollama.generate(prompt, system=PERSONA_GENERATOR_SYSTEM)
        if not persona:
            print("❌ Failed to generate persona (Ollama returned empty). Falling back to default.")
            return load_persona("default")
        return persona
    except Exception as e:
        print(f"❌ An error occurred during persona generation: {e}")
        print("   Falling back to default persona.")
        return load_persona("default")


def run_ai_customer_conversation(
    persona_name=None, scenario=None, mic_name="MacBook Pro Microphone"
):
    """
    Run AI customer conversation loop.
    Replicates manual_voice_test.py conversation logic exactly.

    Returns: path to conversation log file
    """
    # Set up logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"test_run_{timestamp}.txt"

    ollama = OllamaClient()

    # Load or generate persona (raw string, same as manual_voice_test.py)
    if scenario:
        ravi_persona = generate_persona_from_scenario(scenario, ollama)
        print(f'📋 Generated persona from scenario: "{scenario}"')
        print("-" * 60)
        print(ravi_persona)
        print("-" * 60)
    else:
        name = persona_name or "default"
        ravi_persona = load_persona(name)
        print(f"📋 Loaded persona: {name}")

    # Set up microphone
    mic_index = find_microphone_index(mic_name)
    recognizer = sr.Recognizer()

    # Initialize log
    persona_label = persona_name or scenario or "default"
    with open(log_file, "w") as f:
        f.write(f"Persona: {persona_label}\n")
        f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 20 + "\n\n")

    conversation_history = []
    rejected_items = []    # Items the agent has explicitly said are unavailable
    confirmed_updates = [] # Actions the agent has confirmed are already done
    last_offer = None      # Most recent list of options the agent asked Ravi to choose from
    turn = 1

    print("\n🎤 AI Customer (Ravi) is listening for the voice agent...")
    print("   Make sure phone speaker volume is up so computer mic can hear it.")
    print("   Press Ctrl+C to end conversation early.\n")

    try:
        with open(log_file, "a") as log_f:
            while True:
                print(f"--- Turn {turn} ---")

                try:
                    # 1. Listen for the voice agent (phone) speaking
                    with sr.Microphone(device_index=mic_index) as source:
                        recognizer.dynamic_energy_threshold = True
                        recognizer.pause_threshold = 1.0  # slight buffer for TTS pauses between phrases

                        print("\n   🔴 Listening for Agent...")
                        audio = recognizer.listen(source, timeout=45, phrase_time_limit=30)

                    print("   🔄 Transcribing agent's speech...")
                    agent_speech = recognizer.recognize_whisper(audio, model="tiny.en")
                    print(f'   👨‍💼 Agent: "{agent_speech}"')

                    agent_line = f"Agent: {agent_speech}"
                    conversation_history.append(agent_line)
                    log_f.write(agent_line + "\n")

                    if "exit" in agent_speech.lower() or "goodbye" in agent_speech.lower():
                        print("\n🛑 Agent ended the session.")
                        break

                    # Check for agent-side termination conditions.
                    # "cvv" is intentionally excluded: the agent may ask for CVV,
                    # and Ravi must respond with "Yes, the CVV is 358." before ending.
                    agent_lower = agent_speech.lower()
                    order_complete_phrases = [
                        "transfer", "payment",
                        "thank you for your order",
                        "order has been placed", "has been placed",
                        "placed successfully", "order is confirmed",
                        "order confirmed", "successfully placed",
                    ]
                    if any(phrase in agent_lower for phrase in order_complete_phrases):
                        print("\n✅ Agent initiated payment transfer. Ending conversation.")
                        speak_sync("Thank you.")
                        log_f.write("Ravi: Thank you.\n")
                        break

                    # Track items the agent has explicitly said are unavailable.
                    # The full agent sentence is stored so specific sizes/items
                    # can be injected verbatim into the constraint block.
                    rejection_phrases = [
                        "don't have", "do not have", "we don't", "we do not",
                        "not available", "unfortunately", "i'm sorry, we",
                        "sorry, we don't", "sorry, we do not", "i'm sorry,",
                        "can't add", "cannot add",
                    ]
                    if any(p in agent_lower for p in rejection_phrases):
                        if agent_speech.strip() not in rejected_items:
                            rejected_items.append(agent_speech.strip())
                            print(f"   📋 Rejection noted: \"{agent_speech.strip()}\"")

                    # Track when the agent confirms an action is already done.
                    # e.g. "I've already updated your order", "You already have wings"
                    confirmation_phrases = [
                        "i've already", "i have already", "already updated",
                        "already added", "already removed", "already swapped",
                        "already changed", "already included", "already have the",
                        "you already have", "i've updated your order",
                        "i've added", "i've removed", "i've swapped",
                    ]
                    if any(p in agent_lower for p in confirmation_phrases):
                        if agent_speech.strip() not in confirmed_updates:
                            confirmed_updates.append(agent_speech.strip())
                            print(f"   ✅ Confirmation noted: \"{agent_speech.strip()}\"")

                    # Track when the agent offers a list of options to choose from.
                    # Detected when agent asks a question AND lists specific items
                    # (e.g. "We have Pepsi, Diet Pepsi and Mountain Dew. Which would you like?")
                    offer_trigger_phrases = [
                        "we have", "you can choose", "you can pick",
                        "would you like", "which would you", "what size",
                        "what kind", "what flavor", "which size", "which flavor",
                    ]
                    if "?" in agent_speech and any(p in agent_lower for p in offer_trigger_phrases):
                        last_offer = agent_speech.strip()
                        print(f"   🍕 Offer noted: \"{last_offer}\"")

                    # 2. Get AI response.
                    # CRITICAL constraints go FIRST in the prompt so the LLM
                    # reads them before the conversation history. Placing them
                    # after the history causes the model to ignore them because
                    # it anchors on the prior dialogue context.
                    print("   🤖 Ravi is thinking...")
                    prompt = ""
                    has_rules = rejected_items or confirmed_updates or last_offer
                    if has_rules:
                        prompt += "RULES FOR THIS RESPONSE — read these BEFORE the conversation:\n"

                    if rejected_items:
                        prompt += (
                            "The agent has confirmed these items are NOT AVAILABLE.\n"
                            "You MUST NOT mention, request, or reference any of them again "
                            "in any form (including size variants):\n"
                        )
                        for r in rejected_items:
                            prompt += f"  ✗ {r}\n"
                        prompt += "If the agent offered alternatives, pick one of those instead.\n"

                    if confirmed_updates:
                        prompt += (
                            "The agent has ALREADY CONFIRMED these actions are done. "
                            "Do NOT ask for them again, do NOT reference these items as missing or unresolved. "
                            "Treat them as complete:\n"
                        )
                        for c in confirmed_updates:
                            prompt += f"  ✓ {c}\n"
                        if len(confirmed_updates) >= 2:
                            prompt += (
                                "WARNING: You have been repeating yourself. "
                                "The agent has confirmed the same thing multiple times. "
                                "Stop asking about it and move the conversation forward. "
                                "If your order is complete, say so and wrap up the call.\n"
                            )

                    if last_offer:
                        prompt += (
                            f"The agent just asked you to choose. "
                            f"You MUST pick a specific option from what they listed. "
                            f"Do NOT give a vague answer like 'can we just get a drink'.\n"
                            f"Agent's question/offer: \"{last_offer}\"\n"
                        )

                    if has_rules:
                        prompt += "\n"

                    prompt += "Conversation History:\n" + "\n".join(conversation_history)
                    prompt += "\n\nYou are Ravi. Respond with ONLY your spoken words. What do you say next?"

                    ravi_response = ollama.generate(prompt, system=ravi_persona)

                    # 3. Ravi (AI) speaks
                    print(f'   👤 Ravi (AI): "{ravi_response}"')
                    speak_sync(ravi_response)

                    ravi_line = f"Ravi: {ravi_response}"
                    conversation_history.append(ravi_line)
                    log_f.write(ravi_line + "\n")
                    last_offer = None  # Ravi has responded — clear pending offer

                    # 4. Check if Ravi is ending the conversation.
                    # CVV provided → order is done, no need to wait for agent's next turn.
                    end_phrases = ["goodbye", "thanks, bye"]
                    if "cvv" in ravi_response.lower():
                        print("\n✅ Ravi provided CVV. Order complete — ending conversation.")
                        break
                    if any(phrase in ravi_response.lower() for phrase in end_phrases):
                        print("\n✅ Ravi has ended the conversation. Test complete.")
                        break

                except sr.UnknownValueError:
                    print("   ⚠️  Could not understand audio. Please try again.")
                    log_f.write("[Audio not understood]\n")
                    continue
                except sr.RequestError as e:
                    print(f"   Could not request results; {e}")
                    log_f.write(f"[Request Error: {e}]\n")
                    continue

                turn += 1
                print("-" * 60)

    except KeyboardInterrupt:
        print("\n🛑 Session interrupted by user. Exiting.")
    except sr.WaitTimeoutError:
        print("\n\n[Timeout: No speech detected from phone]")
    except Exception as e:
        print(f"\n\n[Error: {e}]")
        import traceback
        traceback.print_exc()

    print(f"\n✅ Conversation saved to: {log_file}")
    return str(log_file)


def find_microphone_index(mic_name):
    """Find microphone by name"""
    import speech_recognition as sr

    mics = sr.Microphone.list_microphone_names()
    for index, name in enumerate(mics):
        if mic_name.lower() in name.lower():
            print(f"  Using microphone: {name}")
            return index
    print(f"  Microphone '{mic_name}' not found, using default")
    return None  # Use default


def run_full_flow(args):
    """
    Full flow: Launch app → AI customer conversation → verify cart
    """
    driver = None
    phase_statuses = {"navigation": "skipped", "conversation": "skipped", "verification": "skipped"}
    start_time = datetime.now()
    log_file = None
    results = {
        "passed": False, "score": 0,
        "matched_items": [], "missing_items": [], "extra_items": [],
        "reasoning": "Test did not complete.", "overview": {},
    }

    try:
        # Clear stale screenshots from previous runs so the report only
        # shows images captured during this run.
        screenshot_dir = Path("config/appium_config.yaml")  # resolve below
        try:
            import yaml
            with open("config/appium_config.yaml") as _f:
                _cfg = yaml.safe_load(_f)
            screenshot_dir = Path(_cfg["test"]["screenshot_dir"])
        except Exception:
            screenshot_dir = Path("/tmp/screenshots")

        if screenshot_dir.is_dir():
            removed = 0
            for f in glob.glob(str(screenshot_dir / "*.png")):
                try:
                    os.remove(f)
                    removed += 1
                except Exception:
                    pass
            if removed:
                print(f"🧹 Cleared {removed} screenshot(s) from previous run in {screenshot_dir}")

        print("\n" + "=" * 70)
        print("PHASE 1: Navigate to Voice Agent")
        print("=" * 70)

        driver = launch_app()
        element = scroll_to_start_voice_order(driver)
        if not element:
            print("❌ Could not find 'Start Voice Order' button")
            phase_statuses["navigation"] = "failed"
            return 1

        click_start_voice_order(driver, element)
        click_arrow_on_ready_screen(driver)
        #grant_microphone_permission(driver)

        agent_active = verify_voice_agent_active(driver)
        if not agent_active:
            print("⚠️  Voice agent verification failed, but continuing...")
            phase_statuses["navigation"] = "failed"
        else:
            phase_statuses["navigation"] = "passed"

        session_id = get_voice_session_id(driver)

        print("\n" + "=" * 70)
        print("PHASE 2: AI Customer Conversation")
        print("=" * 70)
        print("\n🤖 Starting AI customer (Ravi)...")
        print("\nAudio Setup:")
        print("  • Computer speakers playing Ravi's voice → Phone mic hears it")
        print("  • Phone speaker playing agent → Computer mic hears it")
        print("\n🎤 Voice agent is already speaking - starting conversation now...")

        # Run AI customer conversation
        try:
            log_file = run_ai_customer_conversation(
                persona_name=args.persona, scenario=args.scenario, mic_name=args.mic
            )
        except Exception as e:
            print(f"\n❌ AI customer conversation failed: {e}")
            print("   No conversation took place — cart verification cannot proceed.")
            phase_statuses["conversation"] = "failed"
            return 1

        if log_file is None:
            print("\n❌ Conversation ended without producing a log.")
            phase_statuses["conversation"] = "failed"
            return 1

        phase_statuses["conversation"] = "passed"

        print("\n" + "=" * 70)
        print("PHASE 3: Verify Order Complete Screen")
        print("=" * 70)
        # verify_order() waits internally for ORDER COMPLETE screen to appear
        # (polls up to 3 minutes) before navigating to Order Details tab.
        print("\n🔍 Verifying order complete screen...")
        results = verify_order(driver, log_file=log_file)
        phase_statuses["verification"] = "passed" if results["passed"] else "failed"

        print(f"\n{'='*70}")
        print("VERIFICATION RESULTS")
        print(f"{'='*70}")
        print(f"  Status: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")
        print(f"  Score: {results['score']}/100")
        print(f"  Matched: {results['matched_items']}")
        print(f"  Missing: {results['missing_items']}")
        print(f"  Extra: {results['extra_items']}")
        print(f"  Reasoning: {results['reasoning']}")

        # Generate HTML report
        try:
            from src.report_generator import generate_html_report
            report_path = generate_html_report(
                results=results,
                log_file=log_file,
                show_images=args.show_images,
                metadata={
                    "persona": args.persona,
                    "scenario": args.scenario,
                    "mic": args.mic,
                    "session_id": session_id,
                    "start_time": start_time,
                    "end_time": datetime.now(),
                },
                phase_statuses=phase_statuses,
                screenshot_dir=driver.config["test"]["screenshot_dir"],
            )
            print(f"\n📊 HTML Report: {report_path}")
        except Exception as report_err:
            print(f"\n⚠️  Report generation failed: {report_err}")

        return 0 if results["passed"] else 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if driver:
            input("\n👉 Press ENTER to close app and exit...")
            driver.stop()


def run_verify_only(args):
    """Verify cart only (app already open)"""
    driver = None
    try:
        print("\n" + "=" * 70)
        print("VERIFY CART MODE")
        print("=" * 70)
        print("\nAssuming app is already open with cart visible...")

        from src.appium_driver import AppiumDriver

        driver = AppiumDriver("config/appium_config.yaml")
        driver.start()

        log_file = args.log if args.log else None
        results = verify_order(driver, expected_items=args.items, log_file=log_file)

        print(f"\n{'='*70}")
        print("VERIFICATION RESULTS")
        print(f"{'='*70}")
        print(f"  Status: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")
        print(f"  Score: {results['score']}/100")
        print(f"  Matched: {results['matched_items']}")
        print(f"  Missing: {results['missing_items']}")
        print(f"  Extra: {results['extra_items']}")
        print(f"  Reasoning: {results['reasoning']}")

        return 0 if results["passed"] else 1

    finally:
        if driver:
            driver.stop()


def main():
    parser = argparse.ArgumentParser(
        description="End-to-End Voice Ordering Test with AI Customer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full flow with AI customer (default persona)
  python end_to_end_voice_test.py --full

  # Full flow with specific persona
  python end_to_end_voice_test.py --full --persona rushed

  # Full flow with custom scenario
  python end_to_end_voice_test.py --full --scenario "hard of hearing customer"

  # Just verify cart (app already open)
  python end_to_end_voice_test.py --verify-only --log logs/test_run_20260209.txt

  # Verify with expected items
  python end_to_end_voice_test.py --verify-only --items "Large pepperoni" "Garlic knots"

Audio Setup (Physical):
  Position phone near computer speakers so phone mic captures Ravi's voice.
  Position computer mic near phone speaker to capture app voice agent.
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--full",
        action="store_true",
        help="Run full flow with AI customer conversation",
    )
    group.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify cart (assumes app already open)",
    )

    parser.add_argument(
        "--persona", type=str, help="AI customer persona name (from personas/ dir)"
    )
    parser.add_argument(
        "--scenario", type=str, help="Generate persona from scenario text"
    )
    parser.add_argument(
        "--mic",
        type=str,
        default="MacBook Pro Microphone",
        help="Microphone name for capturing phone audio",
    )
    parser.add_argument(
        "--log", type=str, help="Conversation log file for verification"
    )
    parser.add_argument("--items", nargs="+", help="Expected items to verify")

    img_group = parser.add_mutually_exclusive_group()
    img_group.add_argument(
        "--show-images",
        dest="show_images",
        action="store_true",
        default=True,
        help="Embed screenshots in HTML report (default: on)",
    )
    img_group.add_argument(
        "--no-images",
        dest="show_images",
        action="store_false",
        help="Omit screenshots from HTML report",
    )

    args = parser.parse_args()

    if args.full:
        return run_full_flow(args)
    else:
        return run_verify_only(args)


if __name__ == "__main__":
    sys.exit(main())
