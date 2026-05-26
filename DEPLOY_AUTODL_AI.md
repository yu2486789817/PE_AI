# AutoDL 部署 AIChat + Ollama + Yolo_backend

## 推荐结构

Spring Boot 继续放 Render，Supabase 继续做数据库。AutoDL 只跑 AI 服务：

```text
Ollama      127.0.0.1:11434
AIChat      0.0.0.0:5000
Yolo        0.0.0.0:8000
```

Render 后端通过 AutoDL 的公网访问地址调用：

```text
AICHAT_BASE_URL=http(s)://你的AutoDL地址:5000
YOLO_BASE_URL=http(s)://你的AutoDL地址:8000
```

## 1. AutoDL 选镜像

建议选：

```text
Ubuntu 22.04
Python 3.10
PyTorch 2.x
CUDA 11.8 或 12.1
```

GTX 1080 Ti 用 CUDA 11.8 更稳。

## 2. 拉代码

在 AutoDL 终端执行：

```bash
cd /root/autodl-tmp
git clone https://github.com/yu2486789817/PE_AI.git
cd PE_AI
```

如果仓库已经存在：

```bash
cd /root/autodl-tmp/PE_AI
git pull
```

## 3. 启动服务

```bash
cd /root/autodl-tmp/PE_AI
chmod +x Code/deploy/autodl/*.sh
bash Code/deploy/autodl/start_ai_services.sh
```

首次启动会做这些事：

```text
安装 Ollama
启动 Ollama
导入 qwen2.5-pe-sports 模型
创建 Python venv
安装 AIChat 和 Yolo 依赖
启动 AIChat: 5000
启动 Yolo_backend: 8000
```

## 4. 本机健康检查

```bash
bash Code/deploy/autodl/health_ai_services.sh
```

或者：

```bash
curl http://127.0.0.1:5000/api/models
curl http://127.0.0.1:8000/health
```

## 5. AutoDL 公网访问

在 AutoDL 控制台给实例开放/映射端口：

```text
5000 -> AIChat
8000 -> Yolo_backend
```

拿到外网地址后，在 Render 的 Spring Boot 服务环境变量里改：

```text
AICHAT_BASE_URL=<AutoDL的5000公网地址>
YOLO_BASE_URL=<AutoDL的8000公网地址>
```

保存后在 Render 点：

```text
Manual Deploy -> Deploy latest commit
```

## 6. 日志

```bash
tail -f /root/autodl-tmp/PE_AI/logs/aichat.log
tail -f /root/autodl-tmp/PE_AI/logs/yolo.log
tail -f /root/autodl-tmp/PE_AI/logs/ollama.log
```

## 7. 停止服务

```bash
bash Code/deploy/autodl/stop_ai_services.sh
```

## 注意

AutoDL 关机后公网地址可能变化。地址变了，需要同步更新 Render 的：

```text
AICHAT_BASE_URL
YOLO_BASE_URL
```

微信小程序不需要直接访问 AIChat/Yolo，视频上传仍然走 Render Spring Boot。
