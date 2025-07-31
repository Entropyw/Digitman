import paramiko
import time
import sys

# 全局变量
ssh_client = None
channel = None

def connect_to_server():
    global ssh_client, channel
    
    # 服务器的地址和用户名
    server_ip = "10.13.0.9"
    server_username = "wys"
    server_password = "Nwpuwys."

    # 初始化SSH客户端
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 连接到服务器
        ssh_client.connect(server_ip, username=server_username, password=server_password)
        print("成功连接到服务器")
        
        # 打开一个交互式shell通道
        channel = ssh_client.invoke_shell()
        print("打开交互式shell通道")

        cmd = "cd /data/wys/InferLLM/build && ./llama -m chinese-alpaca-7b-q4.bin -g GPU"
        channel.send(cmd + "\n")

        # 等待模型启动完成
        start_time = time.time()
        while time.time() - start_time < 10:  # 最多等待10秒
            if channel.recv_ready():
                output = channel.recv(1024).decode("utf-8", errors="ignore")
                print(f"服务器初始化输出: {output}")
                if ">" in output:  # 假设模型启动后以 ">" 提示
                    break
            time.sleep(0.1)

        print("模型已启动，可以开始对话")
        return True

    except Exception as e:
        print(f"连接或执行命令时出错: {e}")
        return False

def get_char_from_output():
    global channel
    if channel:
        try:
            while not channel.recv_ready():
                time.sleep(0.1)
            output = channel.recv(1024).decode("utf-8", errors="ignore")
            return output
        except Exception as e:
            print(f"读取输出时出错: {e}")
            return None
    else:
        print("通道未初始化")
        return None

def send_message_and_get_response(message):
    global channel
    if channel:
        try:
            channel.send(message + "\n")
            print(f"已发送消息: {message}")
            response = ""
            skip_input = True  # Flag to skip echoed input
            while True:
                output = get_char_from_output()
                if output:
                    if skip_input:
                        # Skip the echoed input until a newline or other marker
                        if "\n" in output:
                            skip_input = False
                        continue
                    if "#" in output:
                        # Stop processing if '#' is encountered
                        output = output[:output.index("#")]
                        if output:
                            response += output
                            yield output
                        break
                    if ">" in output:
                        # Stop at the prompt, yield remaining output if any
                        output = output[:output.index(">")]
                        if output:
                            response += output
                            yield output
                        break
                    response += output
                    yield output
                else:
                    time.sleep(0.1)
            return response
        except Exception as e:
            print(f"发送消息或获取响应时出错: {e}")
            return None
    else:
        print("通道未初始化")
        return None

def main():
    if not connect_to_server():
        print("无法连接到服务器，程序退出")
        return

    try:
        print("输入文本开始对话，输入'exit'或'quit'结束对话")
        while True:
            user_input = input("你: ")
            if user_input.lower() in ['exit', 'quit']:
                print("结束对话。")
                break

            response_generator = send_message_and_get_response(user_input)
            if response_generator:
                print("模型: ", end="", flush=True)
                for output in response_generator:
                    sys.stdout.write(output)
                    sys.stdout.flush()
                print()

    except KeyboardInterrupt:
        print("\n对话被中断")
    finally:
        if ssh_client:
            ssh_client.close()
            print("SSH连接已关闭")

if __name__ == "__main__":
    main()