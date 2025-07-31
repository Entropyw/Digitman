#coding=utf-8
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # 禁用所有GPU，仅使用CPU
import cv2
import numpy as np
from deepface import DeepFace
import face_recognition
import time
import tensorflow as tf
import argparse
import urllib.request

# 不再配置GPU动态内存分配，直接使用CPU

class EmotionRecognizer:
    def __init__(self):
        self.emotion_map = {
            'happy': '高兴', 'sad': '悲伤', 'angry': '愤怒',
            'surprise': '惊讶', 'neutral': '平静', 'disgust': '厌恶'
        }
        self.steadiness_config = {
            'happy': 0.5,
            'sad': 0.8,
            'angry': 1.2,
            'neutral': 0.3,
            'surprise': 0.3,
            'disgust': 6.0
        }
        self.current_emotion = None
        self.current_emotion_start = 0
        self.last_triggered_emotion = None
        # 预初始化模型
        DeepFace.analyze(np.zeros((48, 48, 3), dtype=np.uint8), 
                        actions=['emotion'],
                        enforce_detection=False,
                        silent=True)

    def predict_emotion(self, face_image):
        try:
            result = DeepFace.analyze(face_image, 
                                    actions=['emotion'],
                                    enforce_detection=False,
                                    silent=True,
                                    detector_backend='opencv')
            if isinstance(result, list):
                result = result[0]
            emotion_en = result['dominant_emotion']
            confidence = result['emotion'][emotion_en] / 100.0
            emotion_cn = self.emotion_map.get(emotion_en, '未知')
            self._update_emotion_state(emotion_en, confidence)
            return emotion_en, emotion_cn, confidence
        except Exception as e:
            print(f"预测错误: {str(e)}")
            return 'unknown', '未知', 0.0

    def _update_emotion_state(self, new_emotion, confidence):
        current_time = time.time()
        if confidence < 0.6:
            return
        if new_emotion != self.current_emotion:
            if self.current_emotion is not None:
                duration = current_time - self.current_emotion_start
                print(f"情绪变化: {self.emotion_map[self.current_emotion]} -> {self.emotion_map[new_emotion]}")
            self.current_emotion = new_emotion
            self.current_emotion_start = current_time
            self.last_triggered_emotion = None
        required_duration = self.steadiness_config.get(new_emotion, 1.0)
        elapsed = current_time - self.current_emotion_start
        if elapsed >= required_duration and self.last_triggered_emotion != new_emotion:
            self._trigger_emotion_event(new_emotion)
            self.last_triggered_emotion = new_emotion

    def _trigger_emotion_event(self, emotion_en):
        emotion_cn = self.emotion_map.get(emotion_en, '未知')
        duration = time.time() - self.current_emotion_start
        print(f"事件触发: {emotion_cn} (持续{duration:.1f}秒)")

class MJPEGStreamReader:
    def __init__(self, url):
        self.url = url
        self.stream = None
        self.bytes = b''
        self.connect()
    def connect(self):
        try:
            self.stream = urllib.request.urlopen(self.url)
            print(f"成功连接到视频流: {self.url}")
        except Exception as e:
            print(f"连接视频流失败: {str(e)}")
            self.stream = None
    def read_frame(self):
        if self.stream is None:
            try:
                self.connect()
                if self.stream is None:
                    return False, None
            except:
                return False, None
        try:
            while True:
                self.bytes += self.stream.read(1024)
                a = self.bytes.find(b'\xff\xd8')
                b = self.bytes.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = self.bytes[a:b+2]
                    self.bytes = self.bytes[b+2:]
                    return True, cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"读取视频帧错误: {str(e)}")
            self.stream = None
            return False, None

if __name__ == "__main__":
    recognizer = EmotionRecognizer()
    parser = argparse.ArgumentParser(description='Ubuntu情绪识别客户端-CPU版')
    parser.add_argument('--source', type=str, required=True, 
                        help='Windows主机视频流URL (例如: http://192.168.1.100:5000/video_feed)')
    parser.add_argument('--display', action='store_true', 
                        help='是否显示预览窗口')
    parser.add_argument('--output', type=str, default='', 
                        help='输出视频文件路径')
    args = parser.parse_args()
    stream_reader = MJPEGStreamReader(args.source)
    writer = None
    frame_size = None
    print(f"开始从 {args.source} 读取视频流并进行情绪识别...")
    print("按'q'键退出程序")
    while True:
        ret, frame = stream_reader.read_frame()
        if not ret:
            print("无法读取视频帧，尝试重新连接...")
            time.sleep(1)
            continue
        if args.output and writer is None and frame is not None:
            frame_size = (frame.shape[1], frame.shape[0])
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(args.output, fourcc, 25, frame_size)
        face_locations = face_recognition.face_locations(frame, model="cnn")
        for (top, right, bottom, left) in face_locations:
            try:
                face_img = cv2.resize(frame[top:bottom, left:right], (48, 48))
                emotion_en, emotion_cn, conf = recognizer.predict_emotion(face_img)
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            except Exception as e:
                print(f"处理人脸时错误: {str(e)}")
        if writer and frame is not None:
            writer.write(frame)
        if args.display and frame is not None:
            cv2.imshow('Preview', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    if writer:
        writer.release()
    cv2.destroyAllWindows()