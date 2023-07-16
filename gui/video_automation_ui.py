import os
import traceback
import gradio as gr
from gui.asset_components import start_file
from shortGPT.engine.content_video_engine import ContentVideoEngine, Language
from shortGPT.config.api_db import get_api_key
from shortGPT.gpt import gpt_chat_video
from gui.content_automation_ui import ERROR_TEMPLATE
from enum import Enum

class ChatState(Enum):
    ASK_ORIENTATION = 1
    ASK_LANGUAGE = 2
    ASK_DESCRIPTION = 3
    GENERATE_SCRIPT = 4
    ASK_SATISFACTION = 5
    MAKE_VIDEO = 6
    ASK_CORRECTION = 7 

def isKeyMissing():
    openai_key = get_api_key("OPENAI")
    if not openai_key:
        return "Khóa OpenAI của bạn bị thiếu. Vui lòng chuyển đến tab cấu hình và nhập khóa API."
    
    eleven_labs_key = get_api_key("ELEVEN LABS")
    if not eleven_labs_key:
        return "Khóa API Eleven Labs của bạn bị thiếu. Vui lòng chuyển đến tab cấu hình và nhập khóa API."
    
    eleven_labs_key = get_api_key("PEXELS")
    if not eleven_labs_key:
        return "Khóa API Pexels của bạn bị thiếu. Vui lòng chuyển đến tab config và nhập API key."

def generate_script(message, language):
    return gpt_chat_video.generateScript(message, language)

def correct_script(script, correction):
    return gpt_chat_video.correctScript(script, correction)

def makeVideo(script, language, isVertical, progress):
    shortEngine = ContentVideoEngine(script=script, language=Language(language), isVerticalFormat=isVertical)
    num_steps = shortEngine.get_total_steps()
    progress_counter = 0
    def logger(prog_str):
        progress(progress_counter / (num_steps),f"Tạo video - {progress_counter} - {prog_str}")
    shortEngine.set_logger(logger)
    for step_num, step_info in shortEngine.makeShort():
                progress(progress_counter / (num_steps), f"Tạo video - {step_info}")
                progress_counter += 1

    video_path = shortEngine.get_video_output_path()
    return video_path

def create_video_automation_ui(shortGptUI: gr.Blocks):
        def reset_components():
            return  gr.Chatbot.update(value=intialize_conv()), gr.update(visible=True), gr.HTML.update(value="", visible=False), gr.HTML.update(value="", visible=False)

        def chatbot_conversation():
            global state, isVertical, language, script
            state = ChatState.ASK_ORIENTATION
            isVertical = None
            language = None
            script = ""
            video_html = ""
            videoVisible= False

            def respond(message, chat_history, progress=gr.Progress()):
                global state, isVertical, language, script, videoVisible, video_html
                error_html = ""
                errorVisible = False
                inputVisible= True
                folderVisible= False
                if state == ChatState.ASK_ORIENTATION:
                    errorMessage = isKeyMissing()
                    if errorMessage:
                        bot_message = errorMessage
                    else:     
                        isVertical = "vertical" in message.lower() or "short" in message.lower()
                        state = ChatState.ASK_LANGUAGE
                        bot_message = f"🌐Chọn Ngôn Ngữ Video ({', '.join([lang.value.lower().capitalize() for lang in Language])})"
                elif state == ChatState.ASK_LANGUAGE:
                    language = next((lang for lang in Language if lang.value.lower() in message.lower()), None)
                    language = language if language else Language.ENGLISH
                    state = ChatState.ASK_DESCRIPTION
                    bot_message = "Amazing 🔥 ! 📝Bạn có thể mô tả kỹ lưỡng chủ đề video của mình không? 📝 Tiếp theo tôi sẽ tạo cho bạn một kịch bản dựa trên mô tả đó"
                elif state == ChatState.ASK_DESCRIPTION:
                    script = generate_script(message, language.value)
                    state = ChatState.ASK_SATISFACTION
                    bot_message = f"📝 Đây là tập lệnh đã tạo của bạn: \n\n--------------\n{script}\n\n・Bạn đã hài lòng với tập lệnh chưa và sẵn sàng tiếp tục tạo video chưa? Vui lòng trả lời với 'YES' or 'NO'. 👍👎"
                elif state == ChatState.ASK_SATISFACTION:
                    if "yes" in message.lower():
                        state = ChatState.MAKE_VIDEO
                        inputVisible = False
                        yield gr.update(visible=False), gr.Chatbot.update(value=[[None,"Your video is being made now! 🎬"]]), gr.HTML.update(value="", visible=False), gr.HTML.update(value=error_html, visible=errorVisible), gr.update(visible=folderVisible), gr.update(visible=False)
                        try:
                            video_path = makeVideo(script, language.value, isVertical, progress=progress)
                            file_name = video_path.split("/")[-1].split("\\")[-1]
                            current_url = shortGptUI.share_url+"/" if shortGptUI.share else shortGptUI.local_url
                            file_url_path = f"{current_url}file={video_path}"
                            video_html = f'''
                            <div style="display: flex; flex-direction: column; align-items: center;">
                                <video width="{600}" height="{300}" style="max-height: 100%;" controls>
                                    <source src="{file_url_path}" type="video/mp4">
                                
                                </video>
                                <a href="{file_url_path}" download="{file_name}" style="margin-top: 10px;">
                                    <button style="font-size: 1em; padding: 10px; border: none; cursor: pointer; color: white; background: #007bff;">Download Video</button>
                                </a>
                            </div>'''
                            videoVisible = True
                            folderVisible = True
                            bot_message = "Video của bạn đã hoàn thành!."
                        except Exception as e:
                            traceback_str = ''.join(traceback.format_tb(e.__traceback__))
                            errorVisible = True
                            error_html = ERROR_TEMPLATE.format(error_message=e.args[0], stack_trace=traceback_str)
                            bot_message = "We encountered an error while making this video ❌"
                            print("Error", traceback_str)
                            yield gr.update(visible=False), gr.Chatbot.update(value=[[None,"Video của bạn hiện đang được thực hiện! 🎬"]]), gr.HTML.update(value="", visible=False), gr.HTML.update(value=ERROR_TEMPLATE.format(error_message=e.args[0], stack_trace=traceback_str), visible=errorVisible), gr.update(visible=folderVisible), gr.update(visible=True)
                            
                    else:
                        state = ChatState.ASK_CORRECTION  # change state to ASK_CORRECTION
                        bot_message = "Explain me what you want different in the script"
                elif state == ChatState.ASK_CORRECTION:  # new state
                    script = correct_script(script, message)  # call generateScript with correct=True
                    state = ChatState.ASK_SATISFACTION
                    bot_message = f"📝 Đây là tập lệnh đã sửa của bạn: \n\n--------------\n{script}\n\n・Bạn đã hài lòng với tập lệnh chưa và sẵn sàng tiếp tục tạo video chưa? Vui lòng trả lời với 'YES' or 'NO'. 👍👎"
                chat_history.append((message, bot_message))
                yield gr.update(value="", visible=inputVisible), gr.Chatbot.update(value=chat_history), gr.HTML.update(value=video_html, visible=videoVisible), gr.HTML.update(value=error_html, visible=errorVisible), gr.update(visible=folderVisible), gr.update(visible=True)

            return respond

        def intialize_conv():
            global state, isVertical, language, script, video_html, videoVisible
            state = ChatState.ASK_ORIENTATION
            isVertical = None
            language = None
            script = ""
            video_html = ""
            videoVisible= False
            return [[None, "Bạn muốn video của mình ở định dạng ngang (landscape) hay dọc(vertical)? (landscape OR vertical)"]]                 

        def reset_conversation():
            global state, isVertical, language, script, videoVisible, video_html
            state = ChatState.ASK_ORIENTATION
            isVertical = None
            language = None
            script = ""
            video_html = ""
            videoVisible= False
        
        with gr.Row(visible=False) as video_automation:
            with gr.Column():
                chatbot = gr.Chatbot(intialize_conv, height=365)
                msg = gr.Textbox()
                restart_button = gr.Button("Restart")
                video_folder = gr.Button("📁", visible=False)
                video_folder.click(lambda _: start_file(os.path.abspath("videos/")))
                respond = chatbot_conversation()
                
            errorHTML = gr.HTML(visible=False)
            outHTML = gr.HTML(visible=False)
            restart_button.click(reset_components, [], [chatbot, msg, errorHTML, outHTML])
            restart_button.click(reset_conversation, [])
            msg.submit(respond, [msg, chatbot], [msg, chatbot, outHTML, errorHTML, video_folder, restart_button])
        return video_automation
