import logging
import os
import re
from aiogram import Router, F
from aiogram.types import Message, Voice
from aiogram.enums import ChatAction

logger = logging.getLogger(__name__)
router = Router()
asr_model = None

def init_asr():
    global asr_model
    try:
        from speechbrain.inference.ASR import EncoderDecoderASR
        asr_model = EncoderDecoderASR.from_hparams(source="speechbrain/asr-crdnn-rnnlm-librispeech", savedir="pretrained_models/asr", run_opts={"device": "cpu"})
        logger.info("ASR loaded")
    except Exception as e:
        logger.warning(f"ASR not available: {e}")

async def download_voice(bot, file_id):
    file = await bot.get_file(file_id)
    import tempfile
    path = tempfile.gettempdir() + f"/voice_{file_id}.ogg"
    await file.download_to_drive(path)
    return path

async def transcribe_voice(path):
    global asr_model
    if not asr_model:
        return None
    return asr_model.transcribe_file(path).strip()

@router.message(F.voice)
async def handle_voice_message(message: Message):
    if not asr_model:
        await message.answer("Голосовые сообщения временно недоступны.")
        return
    status = await message.answer("Распознаю голос...")
    path = await download_voice(message.bot, message.voice.file_id)
    if not path:
        await status.edit_text("Ошибка загрузки.")
        return
    transcript = await transcribe_voice(path)
    if transcript:
        from config import config
        import aiohttp
        headers = {"Authorization": f"Bearer {config.OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": config.OPENROUTER_MODEL, "messages": [{"role": "user", "content": transcript}], "max_tokens": 500}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        ai_response = data["choices"][0]["message"]["content"]
                        ai_response = re.sub(r'\*\*(.+?)\*\*', r'\1', ai_response)
                        await status.edit_text(f"📝 Распознано: {transcript}\n\n🧠 {ai_response}")
                    else:
                        await status.edit_text(f"📝 Распознано: {transcript}\n\nОшибка.")
        except Exception as e:
            await status.edit_text(f"📝 Распознано: {transcript}\n\nОшибка связи.")
        os.unlink(path)
    else:
        await status.edit_text("Не удалось распознать речь.")

init_asr()
