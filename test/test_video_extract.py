import cv2
import ffmpeg
import numpy as np
from PIL import Image
from io import BytesIO

import subprocess
import base64
import time
import os
import math
from pathlib import Path
import shutil
import io
from tqdm import tqdm

class VideoConfig:
  #最大分辨率
  MAX_SIZE = (360,420)
  # 目标宽度（像素）
  TARGET_WIDTH = 500  #420 
  
  # 目标高度（像素）
  TARGET_HEIGHT = 360  
  
  #采样帧率
  TARGET_PFS=1.0
  #关键帧最小间隔
  MIN_KEYFRAME_INTERVAL=5
  #最大处理帧数
  MAX_FRAMES=30

def cv_frame_to_base64(frame: cv2.typing.MatLike):
  try:
    if len(frame.shape)==2:
      frame=cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)
    else:
      frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
      
    pil_img=Image.fromarray(frame)
    

    pil_img.thumbnail(VideoConfig.MAX_SIZE,Image.Resampling.LANCZOS)
    
    if pil_img.mode=='RGBA':
      format_type="PNG"
      mine_type="image/png"
    else:
      format_type="JPEG"
      mine_type="image/jpeg"
    
    with BytesIO() as buffered:
      pil_img.save(buffered,
                   format=format_type,
                   quality=95,
                   optimize=True,
                   subsampling=0 if format_type=="JPEG" else None)
      if buffered.tell()==0:
        raise ValueError("buffer为空")
      
      base64_data=base64.b64encode(buffered.getvalue()).decode("utf-8")
      
    
    return f"data:{mine_type};base64,{base64_data}"

  except Exception as e:
    raise e
    
  # frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
  # img=Image.fromarray(frame)
  
  # img.thumbnail((VideoConfig.MAX_PIXELS//420,420))
  # bufferd=BytesIO()
  # img.save(bufferd,format="JPEG")
  # base64_data=base64.b64encode(bufferd.getvalue()).decode("utf-8")
  
  # return f"data:image/jpeg;base64,{base64_data}"
  
  
def extract_key_frame_by_opencv(video_path :str):
  cap=cv2.VideoCapture(video_path)
  if not cap.isOpened():
    raise ValueError("无法打开视频文件")
  
  
  frames=[]
  total_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
  fps=cap.get(cv2.CAP_PROP_FPS)
  interval=int(fps*VideoConfig.MIN_KEYFRAME_INTERVAL)
  
  prev_frame=None
  frame_count=0
  pbar=tqdm(total=VideoConfig.MAX_FRAMES)
  
  while cap.isOpened() and len(frames)<VideoConfig.MAX_FRAMES:
    ret,frame=cap.read()
    if not ret:
      break
    
    if prev_frame is not None:
      diff=cv2.absdiff(frame,prev_frame)
      non_zero=np.count_nonzero(diff)
      if non_zero/diff.size>0.1:
        frames.append(frame)
        pbar.update(1)
        
    else:
      frames.append(frame)
      pbar.update(1)

    prev_frame=frame
    frame_count=frame_count+1
    cap.set(cv2.CAP_PROP_POS_FRAMES,frame_count+interval)
    
    
    
  cap.release()
  return frames[:VideoConfig.MAX_FRAMES]


def extract_key_frame_by_ffmpeg(video_path :str,use_gpu=True):
  
  base_dir = os.path.dirname(os.path.abspath(__file__))
  output_folder=os.path.join(base_dir,"./ffmpeg_output")
  output_folder=Path(output_folder).as_posix()
  
  if os.path.exists(output_folder):
    shutil.rmtree(output_folder)
    
  os.makedirs(output_folder,exist_ok=True)
  try:
    start_time=time.time()
    probe=ffmpeg.probe(video_path)
    video_duration=float(probe["streams"][0]["duration"])
    
    frame_interval=video_duration/VideoConfig.MAX_FRAMES
    
    stream=ffmpeg.input(video_path)
    
    stream=ffmpeg.output(
      stream,
      # os.path.join(output_folder, "frame_%06d.jpg"),
      'pipe:',
      vf=f"fps=1/{frame_interval},scale={VideoConfig.TARGET_WIDTH}:-1",
      vframes=VideoConfig.MAX_FRAMES,
      # q=5,
      format="image2pipe",
      vcodec='mjpeg',
      
    )
    out, _=ffmpeg.run(stream,capture_stdout=True, capture_stderr=True)
    
    frames_base64=[]
    bufferd=BytesIO(out)
    # base64_encoded = base64.b64encode(out).decode('utf-8')
    current_frame = bytearray()
    while True:
      byte = bufferd.read(1)
      if not byte:
        if current_frame:
          frames_base64.append(base64.b64encode(current_frame).decode('utf-8'))
        break
      current_frame.extend(byte)
      
      if len(current_frame) > 2 and current_frame[-2:] == b'\xFF\xD9':  # JPEG 结束标记
        frames_base64.append(base64.b64encode(bytes(current_frame)).decode('utf-8'))
        current_frame = bytearray()
      
    print(f"成功从视频中抽取了 {math.ceil(video_duration * VideoConfig.TARGET_PFS)} 帧, 一共耗时{time.time() - start_time}s")
    return frames_base64
    
  except ffmpeg.Error as e:
    print(f"发生错误{e.stderr}")
      
  
  
  # try:
  #   start_time=time.time()
    
  #   base_dir = os.path.dirname(os.path.abspath(__file__))
  #   output_folder=os.path.join(base_dir,"./ffmpeg_output")
  #   os.makedirs(output_folder,exist_ok=True)
    
  #   command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
  #               "default=nokey=1:noprint_wrappers=1", video_path]
  #   result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  #   if result.returncode != 0:
  #       raise ValueError("Failed to get video duration.")
      
  #   duration = float(result.stdout.decode().strip())
  #   duration=round(duration)
  #   frame_interval=duration/VideoConfig.MAX_FRAMES
    
  #   print(f"视频长度 {duration}")
  #   command=[]
  #   if use_gpu:
  #     command = [
  #           "ffmpeg",
  #           "-hwaccel", "cuda",  # GPU 解码
  #           "-i", video_path,
  #           "-vf", f"fps=1/{frame_interval},scale={VideoConfig.TARGET_WIDTH}:-1",  # GPU 缩放
  #           "-frames:v", str(VideoConfig.MAX_FRAMES),
  #           # "-f", "image2",  # 输出图像序列
  #           # "-vcodec", "mjpeg",  # 输出 JPEG
  #           "-vcodec", "h264_nvenc",  # GPU 编码为 H.264
  #           "-preset", "fast",
  #           # "-q:v", "5",  # JPEG 质量（2-31，值越小质量越高）
  #           # os.path.join(output_folder, "frame_%06d.jpg")  # 输出到临时文件
  #           os.path.join(output_folder, "output.h264")
  #       ]
  #     process = subprocess.run(command, capture_output=True)
  #     print(f"一共耗时{time.time() - start_time}s")
  #     if process.returncode != 0:
  #         print(f"错误: {process.stderr}")
  #         return None
      
      
    
  #   else:
  #     command = [
  #           "ffmpeg",
  #           "-hwaccel","cuda",
  #           "-i", video_path,
  #           "-vf", f"fps=1/{frame_interval},scale={VideoConfig.TARGET_WIDTH}:-1",
  #           "-frames:v",str(VideoConfig.MAX_FRAMES),
  #           "-f","image2pipe",
  #           "-vcodec",'mjpeg',
  #           'pipe:'
  #       ]
  #     process=subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  #     out, err = process.communicate()
  #     frames_base64=[]
  #     bufferd=BytesIO(out)
  #     # base64_encoded = base64.b64encode(out).decode('utf-8')
  #     current_frame = bytearray()
  #     while True:
  #       byte = bufferd.read(1)
  #       if not byte:
  #         if current_frame:
  #           frames_base64.append(base64.b64encode(current_frame).decode('utf-8'))
  #         break
  #       current_frame.extend(byte)
        
  #       if len(current_frame) > 2 and current_frame[-2:] == b'\xFF\xD9':  # JPEG 结束标记
  #         frames_base64.append(base64.b64encode(bytes(current_frame)).decode('utf-8'))
  #         current_frame = bytearray()
        
  #     print(f"成功从视频中抽取了 {math.ceil(duration * VideoConfig.TARGET_PFS)} 帧, 一共耗时{time.time() - start_time}s")
  #     return frames_base64
    
  # except ffmpeg.Error as e:
  #   print(f"发生错误{e.stderr}")
  
  # print(f"成功从视频中抽取了 {math.ceil(duration * VideoConfig.TARGET_PFS)} 帧, 一共耗时{time.time() - start_time}s")

def display_base64_frame(base64_string):
    img_data = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_data))
    img.show()
    
if __name__=="__main__":
  
  video_path=r"C:\Users\hansolo\Videos\京都动画\1、轻音少女！+NCED.mp4"
  
  # frames=extract_key_frame_by_opencv(video_path)
  
  # for frame in frames:
  #   base64_data=cv_frame_to_base64(frame)
    
  #   print(base64_data)
  #   break
  
  base64_frames=extract_key_frame_by_ffmpeg(video_path=video_path,use_gpu=False)
  # print(base64_frames[0])
  display_base64_frame(base64_frames[14])