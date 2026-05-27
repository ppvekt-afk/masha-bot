import logging
from google.cloud import texttospeech

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.client = None
    
    def initialize(self):
        try:
            self.client = texttospeech.TextToSpeechClient()
            logger.info("TTS готов")
        except Exception as e:
            logger.warning(f"TTS не доступен: {e}")
    
    def synthesize(self, text: str) -> bytes:
        if not self.client:
            return None
        try:
            input_text = texttospeech.SynthesisInput(text=text[:500])
            voice = texttospeech.VoiceSelectionParams(
                language_code="ru-RU",
                name="ru-RU-Wavenet-D",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.OGG_OPUS,
                speaking_rate=0.95
            )
            response = self.client.synthesize_speech(input=input_text, voice=voice, audio_config=config)
            return response.audio_content
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None

tts_service = TTSService()
