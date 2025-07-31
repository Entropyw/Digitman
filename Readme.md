## Step1  运行windows_camera_server脚本

终端输入：python windows_camera_server.py --camera 0 --port 5000

代码的功能是使用本机摄像头，将视频流上传到端口5000

## Step2 下载ngrok工具

<[利用ngrok实现内网穿透（全网最详细教程）_ngrok内网穿透-CSDN博客](https://blog.csdn.net/Myon5/article/details/134626288)>

这是我找到的配置教程

其中一步更改为ngrok http 5000

下载后确实是需要以管理员的身份运行

映射5000端口到公网

运行成功后会如图显示

![image-20250519230430862](Readme.assets/image-20250519230430862.png)

需要点击http://localhost:5000/启动摄像头

## Step3 服务器中运行ubuntu_emotion_client1

命令行输入：python ubuntu_emotion_client.py --source https://c9c7-124-114-148-18.ngrok-free.app/video_feed

==注意：每次ngrok生成的https://c9c7-124-114-148-18.ngrok-free.app不同，每次需要更改参数==

可使用curl -I https://c9c7-124-114-148-18.ngrok-free.app测试连接

代码在人脸识别部分未做改变，只是在处理视频流进行了处理

仍是在_trigger_emotion_event函数内增加相应情绪反应