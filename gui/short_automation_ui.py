import traceback
import gradio as gr
from gui.asset_components import background_video_checkbox, background_music_checkbox, start_file
from shortGPT.config.api_db import get_api_key
from shortGPT.engine.reddit_short_engine import RedditShortEngine, Language
from shortGPT.engine.facts_short_engine import FactsShortEngine
import time
language_choices = [lang.value.upper() for lang in Language]
import gradio as gr
import random
import os
import time
ERROR_TEMPLATE = """
<div style='text-align: center; background: #9fcbc3; color: #3f4039; 
padding: 20px; border-radius: 5px; margin: 10px;'>
    <h2 style='margin: 0;'>ERROR : {error_message}</h2>
    <p style='margin: 10px 0;'>Traceback Info : {stack_trace}</p>
</div>"""


def create_short_automation_ui(shortGptUI: gr.Blocks):
    def create_short(numShorts,
            short_type,
            language,
            numImages,
            watermark,
            background_video_list,
            background_music_list,
            facts_subject,
            progress=gr.Progress()):
        
        numShorts = int(numShorts)
        numImages = int(numImages) if numImages else None
        background_videos = (background_video_list * ((numShorts // len(background_video_list)) + 1))[:numShorts]
        background_musics = (background_music_list * ((numShorts // len(background_music_list)) + 1))[:numShorts]
        language = Language(language.lower())
        embedHTML = '<div style="display: flex; overflow-x: auto; gap: 20px;">'
        progress_counter = 0
        try:
            for i in range(numShorts):
                shortEngine = create_short_engine(short_type=short_type,
                                                    language=language,
                                                    numImages=numImages,
                                                background_video=background_videos[i],
                                                background_music=background_musics[i],
                                                watermark=watermark,
                                                facts_subject=facts_subject
                                                )
                num_steps = shortEngine.get_total_steps()
                def logger(prog_str):
                    progress(progress_counter / (num_steps * numShorts),f"Making short {i+1}/{numShorts} - {prog_str}")
                shortEngine.set_logger(logger)
                
                for step_num, step_info in shortEngine.makeShort():
                    progress(progress_counter / (num_steps * numShorts), f"Making short {i+1}/{numShorts} - {step_info}")
                    progress_counter += 1

                video_path = shortEngine.get_video_output_path()
                current_url = shortGptUI.share_url+"/" if shortGptUI.share else shortGptUI.local_url
                file_url_path = f"{current_url}file={video_path}"
                file_name = video_path.split("/")[-1].split("\\")[-1]
                embedHTML += f'''
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <video width="{250}" height="{500}" style="max-height: 100%;" controls>
                        <source src="{file_url_path}" type="video/mp4">
                        
                    </video>
                    <a href="{file_url_path}" download="{file_name}" style="margin-top: 10px;">
                        <button style="font-size: 1em; padding: 10px; border: none; cursor: pointer; color: white; background: #007bff;">Tải Video</button>
                    </a>
                </div>'''
                yield embedHTML + '</div>', gr.Button.update(visible=True), gr.update(visible=False)

        except Exception as e:
            traceback_str = ''.join(traceback.format_tb(e.__traceback__))
            print("Error", traceback_str)
            yield embedHTML + '</div>', gr.Button.update(visible=True), gr.update(value=ERROR_TEMPLATE.format(error_message=e.args[0], stack_trace=traceback_str), visible=True)
        
        
        
        
    with gr.Row(visible=False) as short_automation:
        with gr.Column():
            numShorts = gr.Number(label="Number of shorts", minimum=1, value=1)
            short_type = gr.Radio(["Reddit Story shorts","Historical Facts shorts", "Scientific Facts shorts", "Tuỳ Chỉnh Facts shorts"], label="Chọn Kiểu Video Short", value="Custom Facts", interactive=True)
            facts_subject = gr.Textbox(label="Write a subject for your facts (example: Football facts)",interactive=True, visible=False)
            short_type.change(lambda x: gr.update(visible=x=="Tuỳ Chỉnh Facts shorts"),[short_type],[facts_subject] )
            language = gr.Radio(language_choices, label="Language", value="ENGLISH")

            useImages = gr.Checkbox(label="Use images", value=True)
            numImages = gr.Radio([5, 10, 25],value=25, label="Số lượng hình ảnh mỗi Short", visible=True, interactive=True)
            useImages.change(lambda x: gr.update(visible=x), useImages, numImages)

            addWatermark = gr.Checkbox(label="Thêm watermark")
            watermark = gr.Textbox(label="Watermark (Tên Channel)", visible=False)
            addWatermark.change(lambda x: gr.update(visible=x), [addWatermark], [watermark])

            background_video_checkbox.render()
            background_music_checkbox.render()

            createButton = gr.Button(label="Tạo Video Shorts")

            generation_error = gr.HTML(visible=False)
            video_folder = gr.Button("📁", visible=True)
            output = gr.HTML()

        video_folder.click(lambda _: start_file(os.path.abspath("videos/")))

        createButton.click(inspect_create_inputs, inputs=[background_video_checkbox, background_music_checkbox, watermark,short_type, facts_subject], outputs=[generation_error]).success(create_short, inputs=[
            numShorts,
            short_type,
            language,
            numImages,
            watermark,
            background_video_checkbox,
            background_music_checkbox,
            facts_subject
        ], outputs=[output, video_folder, generation_error])
    return short_automation




def inspect_create_inputs(
    background_video_list,
    background_music_list, 
    watermark,
    short_type,
    facts_subject
    ):
    if short_type == "Custom Facts shorts":
        if not facts_subject:
            raise gr.Error("Vui lòng viết ra chủ đề video")
    if not background_video_list:
        raise gr.Error("Vui lòng chọn ít nhất một video nền.")

    if not background_music_list:
        raise gr.Error("Vui lòng chọn ít nhất một nhạc nền.")
    
    if watermark != "":
        if not watermark.replace(" ", "").isalnum():
            raise gr.Error("Hình mờ chỉ nên chứa chữ cái và số.")
        if len(watermark) > 25:
            raise gr.Error("Hình mờ không được vượt quá 25 ký tự.")
        if len(watermark) < 3:
            raise gr.Error("Hình mờ phải dài ít nhất 3 ký tự.")
    
    openai_key = get_api_key("OPENAI")
    if not openai_key:
        raise gr.Error("Khóa API OPENAI bị thiếu. Vui lòng chuyển đến tab cấu hình và nhập khóa API.")
    
    eleven_labs_key = get_api_key("ELEVEN LABS")
    if not eleven_labs_key:
        raise gr.Error("Khóa API ELEVEN LABS bị thiếu. Vui lòng chuyển đến tab cấu hình và nhập khóa API.")
    return gr.update(visible=False)

def update_progress(progress, progress_counter, num_steps, num_shorts, stop_event):
    start_time = time.time()
    while not stop_event.is_set():
        elapsed_time = time.time() - start_time
        dynamic = int(3649 * elapsed_time / 600)
        progress(progress_counter / (num_steps * num_shorts), f"Step 12 in progress - {dynamic}/3649")
        time.sleep(0.1)  # update every 0.1 second

def create_short_engine(short_type, language, numImages,
        watermark,
        background_video,
        background_music,
        facts_subject):
    watermark = watermark.upper() if watermark else None
    if short_type == "Reddit Story shorts":
        return RedditShortEngine(background_video_name=background_video,
                                            background_music_name=background_music,
                                            num_images=numImages,
                                            watermark=watermark,
                                            language=language)
    if "fact" in  short_type.lower():
        if "custom" in short_type.lower():
            facts_subject = facts_subject
        else:
            facts_subject = short_type
        return FactsShortEngine(facts_type=facts_subject, background_video_name=background_video,
                                            background_music_name=background_music,
                                            num_images=50,
                                            watermark=watermark,
                                            language=language)
    raise gr.Error(f"Short type does not have a valid short engine: {short_type}")
            
