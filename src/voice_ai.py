"""
Voice AI integration - Text-to-Speech using edge-tts (high quality, consistent)
"""

import edge_tts
import asyncio
import time
import os
import subprocess


class VoiceAI:
    """Voice synthesis for test automation - uses Microsoft Edge TTS"""

    def __init__(
        self, voice: str = "en-US-GuyNeural", audio_dir: str = "/tmp/pizza_voice_test"
    ):
        self.voice = voice  # Use a consistent neural voice
        self.audio_dir = audio_dir
        os.makedirs(audio_dir, exist_ok=True)

        # Clean up old temp files on initialization
        self._cleanup_old_files()

    def _cleanup_old_files(self):
        """Clean up temp files older than 1 hour"""
        try:
            import glob
            import time

            # Clean up WAV files older than 1 hour
            cutoff_time = time.time() - 3600  # 1 hour ago

            for wav_file in glob.glob(f"{self.audio_dir}/*.wav"):
                try:
                    if os.path.getmtime(wav_file) < cutoff_time:
                        os.unlink(wav_file)
                        print(
                            f"   🗑️ Cleaned up old temp file: {os.path.basename(wav_file)}"
                        )
                except OSError:
                    pass

            # Keep only last 10 files to prevent disk space issues
            wav_files = sorted(
                glob.glob(f"{self.audio_dir}/*.wav"), key=os.path.getmtime, reverse=True
            )
            if len(wav_files) > 10:
                for old_file in wav_files[10:]:
                    try:
                        os.unlink(old_file)
                        print(
                            f"   🗑️ Cleaned up excess temp file: {os.path.basename(old_file)}"
                        )
                    except OSError:
                        pass

        except Exception as e:
            print(f"   ⚠️ Temp file cleanup warning: {e}")

    async def speak(self, text: str, filename: str = "utterance"):
        """Generate and play speech using edge-tts"""
        print(f"🔊 Speaking: '{text}'")
        wav_file = None
        try:
            timestamp = str(int(time.time() * 1000))
            wav_file = f"{self.audio_dir}/{filename}_{timestamp}.wav"

            print(f"   📝 Generating audio...")

            # Use edge-tts to generate audio
            communicate = edge_tts.Communicate(text, voice=self.voice)
            await communicate.save(wav_file)

            print(f"   🔊 Playing audio...")
            # Play the audio file
            subprocess.run(["afplay", wav_file], check=True, timeout=60)

            print(f"   ✅ Audio spoken")
            return wav_file

        except Exception as e:
            print(f"   ❌ TTS Error: {str(e)}")
            import traceback

            traceback.print_exc()
            return None
        finally:
            # Clean up the temp file immediately after playing
            if wav_file and os.path.exists(wav_file):
                try:
                    os.unlink(wav_file)
                    print(f"   🗑️ Cleaned up temp audio file")
                except OSError:
                    pass


def speak_sync(text: str, voice: str = "en-US-GuyNeural"):
    """Synchronous wrapper for speaking text"""
    vai = VoiceAI(voice=voice)
    import asyncio

    return asyncio.run(vai.speak(text))
