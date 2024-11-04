import yt_dlp
import ffmpeg
import os
from vertexai.generative_models import GenerationConfig
from gemini import generate, generate_video
import time


url = "https://www.youtube.com/watch?v=MaJmUUtr2SI"

generation_config = GenerationConfig(
    max_output_tokens = 8192,
    temperature = 0,
    top_p = 0.95,
    response_mime_type= "application/json",
    response_schema = {"type": "OBJECT","properties": {"srt": {"type": "STRING"}}} )


def download_video(url):
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',  # 使用视频标题作为文件名
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 首先获取视频信息但不下载
            info = ydl.extract_info(url, download=False)
            filename = f"{info['title']}.{info['ext']}"
            
            # 检查文件是否已经存在
            if os.path.exists(filename):
                print(f"文件 '{filename}' 已存在，跳过下载")
                return filename
            else:
                print(f"开始下载: {filename}")
                # 下载视频
                ydl.download([url])
                return filename
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None

filename=download_video(url)

prompt = """
## Task
- Transcribe this video

## Rules
- Label each line of your subtitles, starting with 1.
- Enter the timecode to indicate how long the text should stay on the screen.
- Type in the text you wish to appear.
- Output with SRT format.

## Example
1
00:01:17,757 --> 00:01:18,757
Copy boy!

2
00:01:20,727 --> 00:01:23,662
Where's the rest of this story?
"""

print("生成原语言字幕中...")

start_time = time.time()
response = generate_video(prompt, filename, generation_config)
end_time = time.time()
spend_time = end_time - start_time
print("花费时间：", spend_time, "秒")
text = response['srt']

print("将字幕翻译成中文...")
prompt = f"""
## Task
- Translate the content to Chinese.

## Rules
- Output with SRT format.

## Input
%s
""" % text

response = generate(prompt, generation_config)
text = response['srt']


subtitle_file = filename+".srt"
def text_to_srt(text):
    lines = text.splitlines()
    with open(subtitle_file, "w") as f:
        for line in lines:
            line = line.replace("。", "")
            f.write(line+'\n')

text_to_srt(text)
print("字幕文件名称：", filename+".srt")


def combain_srt(input_file, output_file, subtitle_file):
    try:
        # 获取输入流
        stream = ffmpeg.input(input_file)
        # 分离视频和音频流
        v = stream.video
        a = stream.audio
        # 对视频流添加字幕
        v = ffmpeg.filter(v, 'subtitles', subtitle_file, force_style='FontName=Academy Engraved LET')
        # 合并视频和音频流并输出
        stream = ffmpeg.output(v, a, output_file, acodec='copy')
        ffmpeg.run(stream, quiet=True)
    except ffmpeg.Error as e:
        print("转换失败:", e.stderr.decode())


print("将字幕嵌入视频中...")
start_time = time.time()
combain_srt(filename,'srt_'+filename, subtitle_file)
end_time = time.time()
spend_time = end_time - start_time
print("花费时间：", spend_time, "秒")
print("视频处理完成！")