#coding=utf-8
from flask import Flask, Response, redirect
import cv2
import argparse

app = Flask(__name__)

def generate_frames(camera):
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # 将帧编码为JPEG格式
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # 使用MJPEG格式传输视频流
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """根路径重定向到视频流页面"""
    return redirect('/video_feed')

@app.route('/video_feed')
def video_feed():
    """提供视频流的HTTP接口"""
    return Response(generate_frames(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Windows摄像头流服务器')
    parser.add_argument('--camera', type=int, default=0, 
                        help='摄像头索引 (默认: 0)')
    parser.add_argument('--width', type=int, default=640, 
                        help='视频宽度 (默认: 640)')
    parser.add_argument('--height', type=int, default=480, 
                        help='视频高度 (默认: 480)')
    parser.add_argument('--port', type=int, default=5000, 
                        help='服务器端口 (默认: 5000)')
    args = parser.parse_args()
    
    # 初始化摄像头
    camera = cv2.VideoCapture(args.camera)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    
    # 检查摄像头是否成功打开
    if not camera.isOpened():
        print(f"错误: 无法打开摄像头 {args.camera}")
        exit(1)
    
    print(f"启动摄像头流服务器在 http://localhost:{args.port}/")
    print(f"本地访问视频流: http://localhost:{args.port}/video_feed")
    print(f"在Ubuntu服务器上使用以下URL访问: http://[你的Windows IP地址]:{args.port}/")
    print(f"如果使用ngrok等工具映射，请访问映射后的完整URL，例如: https://xxxx.ngrok.io/")
    print("按Ctrl+C停止服务器")
    
    # 启动服务器，允许外部访问
    app.run(host='0.0.0.0', port=args.port, threaded=True)