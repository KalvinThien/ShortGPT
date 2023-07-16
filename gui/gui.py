import gradio as gr
from gui.config_ui import create_config_ui
from gui.asset_library_ui import create_asset_library_ui
from gui.content_automation_ui import create_content_automation
max_choices = 20
ui_asset_dataframe = gr.Dataframe(interactive=False)

LOGO_DIM = 64
def run_app(colab=False):
    with gr.Blocks(css="footer {visibility: hidden}", title="Auto Video" ) as shortGptUI:
        with gr.Row(variant='compact'):
            gr.HTML(f'''
            
            ''')
        content_automation = create_content_automation(shortGptUI)
        asset_library_ui = create_asset_library_ui()
        config_ui = create_config_ui()
    shortGptUI.queue(concurrency_count=5, max_size=20).launch(server_port=31415, height=1000, share=colab)
if __name__ == "__main__":
    run_app()
