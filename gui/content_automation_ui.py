import gradio as gr

from gui.ui_tab_short_automation import ShortAutomationUI
from gui.ui_tab_video_automation import VideoAutomationUI
from gui.ui_tab_video_translation import VideoTranslationUI


class GradioContentAutomationUI:
    def __init__(self, shortGPTUI):
        self.shortGPTUI = shortGPTUI
        self.content_automation_ui = None

    def create_ui(self):
        '''Create Gradio interface'''
        with gr.Tab("Tự động hóa nội dung") as self.content_automation_ui:
            gr.Markdown("# 🏆 Tự động hóa nội dung 🚀")
            gr.Markdown("## Chọn nhiệm vụ tự động hóa mong muốn của bạn.")
            choice = gr.Radio(['🎬 Tự động hóa việc tạo video short', '🎞️ Tự động hóa video với  kho có sẵn', '🌐 Dịch video qua ngôn ngữ khác'], label="Chọn một tùy chọn")
            video_automation_ui = VideoAutomationUI(self.shortGPTUI).create_ui()
            short_automation_ui = ShortAutomationUI(self.shortGPTUI).create_ui()
            video_translation_ui = VideoTranslationUI(self.shortGPTUI).create_ui()
            choice.change(lambda x: (gr.update(visible=x == choice.choices[1]), gr.update(visible=x == choice.choices[0]), gr.update(
                visible=x == choice.choices[2])), [choice], [video_automation_ui, short_automation_ui, video_translation_ui])
        return self.content_automation_ui
