from your_edge_tts_api_module import generateVoice
from shortGPT.audio.voice_module import VoiceModule

class EdgeTTSVoiceModule(VoiceModule):
    def __init__(self, api_key, voiceName):
        self.api_key = api_key
        self.voiceName = voiceName
        super().__init__()

    def generate_voice(self, text, outputfile):
        file_path = generateVoice(text=text, voice=self.voiceName, fileName=outputfile, api_key=self.api_key)
        return file_path
