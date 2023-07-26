import edge_tts
from shortGPT.audio.voice_module import VoiceModule
import asyncio

voices = {
    'vi': {'Male': 'vi-VN-NamMinhNeural', 'Female': 'vi-VN-HoaiMyNeural'},
    'en': {'Male': 'en-US-SteffanNeural', 'Female': 'en-US-AriaNeural'},
    'ms': {'Male': 'ms-MY-OsmanNeural', 'Female': 'ms-MY-YasminNeural'},
    'lo': {'Male': 'lo-LA-SouvanhNeural', 'Female': 'lo-LA-VilayNeural'},
    'th': {'Male': 'th-TH-NiwatNeural', 'Female': 'th-TH-PremwadeeNeural'},
    'my': {'Male': 'my-MM-ThihaNeural', 'Female': 'my-MM-NilarNeural'},
    # thêm những ngôn ngữ khác tại đây
}

# Tạo ánh xạ từ tên ngôn ngữ đầy đủ sang mã ngôn ngữ
language_names = {
    "Vietnamese": "vi",
    "English": "en",
    "Malaysia": "ms",
    "Lao": "lo",
    "ThaiLan": "th",
    "Myanmar": "my",
}

class EdgeTTSVoiceModule(VoiceModule):
    def __init__(self, voiceName, language):
        language_code = language_names[language]
        self.voiceName = voices[language_code][voiceName]
        super().__init__()

    async def generate_voice(self, text, outputfile):
        communicate = edge_tts.Communicate(text, self.voiceName)
        with open(outputfile, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
        return outputfile
