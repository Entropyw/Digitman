import os
import time
import logging
import tempfile
import json
import subprocess
import datetime
from typing import Dict, Any, Optional, List
import uuid
import pyttsx3
import whisper
import speech_recognition as sr

class SpeechService:
    """语音服务核心类，提供语音转文字和文字转语音功能"""
    
    def __init__(self):
        # 初始化日志
        self._setup_logging()
        
        # 初始化模型和引擎
        self.whisper_model = None
        self.tts_engine = pyttsx3.init()
        
        # 创建文件存储目录
        self.audio_files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio_files")
        self.json_files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json_files")
        os.makedirs(self.audio_files_dir, exist_ok=True)
        os.makedirs(self.json_files_dir, exist_ok=True)

    def _setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("speech_service")

    def get_whisper_model(self):
        """延迟加载Whisper模型"""
        if self.whisper_model is None:
            try:
                self.logger.info("正在加载Whisper模型...")
                self.whisper_model = whisper.load_model("small")
                self.logger.info("Whisper模型加载完成")
            except Exception as e:
                self.logger.error(f"加载Whisper模型失败: {e}")
                raise RuntimeError(f"无法加载语音识别模型: {e}")
        return self.whisper_model

    def convert_to_whisper_format(self, input_path: str, output_path: Optional[str] = None) -> str:
        """转换音频格式为Whisper推荐格式(16kHz, mono, wav)"""
        if output_path is None:
            output_path = input_path.replace('.wav', '_converted.wav')

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"找不到音频文件: {input_path}")

        command = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-ar', '16000',
            '-ac', '1',
            '-f', 'wav',
            output_path
        ]

        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"音频转换失败: {e}")
        return output_path

    def process_speech(self, audio_path: str) -> Dict[str, Any]:
        """处理语音并返回识别文本"""
        try:
            model = self.get_whisper_model()
            converted_path = self.convert_to_whisper_format(audio_path)
            result = model.transcribe(converted_path, language='zh')
            recognized_text = result["text"]
            self.logger.info(f"语音识别结果: {recognized_text}")

            try:
                if os.path.exists(converted_path) and converted_path != audio_path:
                    os.unlink(converted_path)
            except Exception as e:
                self.logger.warning(f"删除转换后的音频文件失败: {str(e)}")

            return {
                "text": recognized_text,
                "success": True
            }
                
        except Exception as e:
            self.logger.error(f"语音识别错误: {str(e)}")
            raise RuntimeError(f"语音识别错误: {str(e)}")

    def speech_to_text(self, audio_data: bytes) -> Dict[str, Any]:
        """语音转文本主函数"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            self.logger.info("临时音频文件已保存，开始进行语音识别")
            
            try:
                result = self.process_speech(tmp_path)
                timestamp = int(time.time())
                json_filename = f"stt_{timestamp}.json"
                json_filepath = os.path.join(self.json_files_dir, json_filename)
                
                json_data = {
                    "text": result["text"],
                }
                
                with open(json_filepath, 'w', encoding='utf-8') as json_file:
                    json.dump(json_data, json_file, ensure_ascii=False, indent=4)
                    
                self.logger.info(f"语音识别结果已保存到JSON文件: {json_filepath}")
                
                return result
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception as e:
                        self.logger.warning(f"删除临时文件失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"语音识别错误: {str(e)}")
            raise RuntimeError(f"语音识别错误: {str(e)}")

    def text_to_speech(self, text: str, rate: Optional[int] = 200, voice: Optional[str] = None) -> Dict[str, Any]:
        """文本转语音主函数"""
        try:
            text = text.strip()
            if not text:
                raise ValueError("文本不能为空")
            
            if rate is not None:
                self.tts_engine.setProperty('rate', rate)
                self.logger.info(f"设置语速为: {rate}")
            
            if voice is not None:
                voices = self.tts_engine.getProperty('voices')
                for v in voices:
                    if voice in v.id or voice in v.name:
                        self.tts_engine.setProperty('voice', v.id)
                        self.logger.info(f"设置音色为: {v.name} (ID: {v.id})")
                        break
            
            timestamp = int(time.time())
            audio_filename = f"tts_{timestamp}.mp3"
            audio_filepath = os.path.join(self.audio_files_dir, audio_filename)
            
            self.tts_engine.save_to_file(text, audio_filepath)
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            
            self.logger.info(f"文本已转换为语音并保存到: {audio_filepath}")
            
            current_rate = self.tts_engine.getProperty('rate')
            current_voice = self.tts_engine.getProperty('voice')
            voice_name = "默认"
            voices = self.tts_engine.getProperty('voices')
            for v in voices:
                if v.id == current_voice:
                    voice_name = v.name
                    break
            
            return {
                "success": True, 
                "message": "文本已转换为语音并播放",
                "audio_file": audio_filename,
                "audio_path": audio_filepath,
                "rate": current_rate,
                "voice": voice_name
            }
        except Exception as e:
            self.logger.error(f"文本转语音错误: {str(e)}")
            raise RuntimeError(f"文本转语音错误: {str(e)}")

    def get_available_voices(self) -> Dict[str, Any]:
        """获取系统可用的所有语音音色"""
        try:
            voices = self.tts_engine.getProperty('voices')
            voice_list = []
            
            for voice in voices:
                voice_list.append({
                    "id": voice.id,
                    "name": voice.name,
                    "languages": voice.languages,
                    "gender": getattr(voice, 'gender', 'unknown'),
                    "age": getattr(voice, 'age', 'unknown')
                })
            
            return {
                "success": True,
                "voices": voice_list,
                "current_voice": self.tts_engine.getProperty('voice'),
                "current_rate": self.tts_engine.getProperty('rate')
            }
        except Exception as e:
            self.logger.error(f"获取音色列表错误: {str(e)}")
            raise RuntimeError(f"获取音色列表错误: {str(e)}")

    def real_time_speech_to_text(self, callback, stop_event):
        """实时语音识别"""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("正在监听...")
            while not stop_event.is_set():
                try:
                    audio = recognizer.listen(source, timeout=1)
                    text = recognizer.recognize_google(audio, language='zh-CN')
                    callback(text)
                except sr.WaitTimeoutError:
                    pass  # 停顿时继续监听
                except sr.UnknownValueError:
                    print("无法识别语音")
                except sr.RequestError as e:
                    print(f"请求错误: {e}")

if __name__ == "__main__":
    speech_service = SpeechService()
    voices_info = speech_service.get_available_voices()
    print(json.dumps(voices_info, indent=2, ensure_ascii=False))
    print("\n文本转语音测试:")
    tts_result = speech_service.text_to_speech(
        text="你好，这是一个测试文本",
        rate=150,
        voice=None
    )
    print(f"生成的语音文件: {tts_result['audio_path']}")