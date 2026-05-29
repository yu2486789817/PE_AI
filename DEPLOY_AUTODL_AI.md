# AutoDL 部署 AIChat + Ollama + Yolo_backend

> 有两种实例可选：
> - **GPU 实例**：见下方原始流程（第 1~7 节），用 `start_ai_services.sh`。
> - **纯 CPU 实例**（租不到卡时的省钱方案）：见文末「纯 CPU 实例部署」，用 `start_ai_services_cpu.sh` + cloudflared 隧道。

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

---

# 纯 CPU 实例部署（无 GPU / 省钱方案）

租不到 GPU 时，可用 AutoDL 的纯 CPU 实例（如 32 核 EPYC/Xeon + 60~120GB 内存）。
`yolov8n-pose` 是最小姿态模型，作业视频是异步批处理（非实时），多核 CPU 足够；
聊天用的是 3B + Q4 量化 GGUF，Ollama 在无 GPU 时自动回退 CPU。

## C1. 选实例

```text
镜像：Ubuntu 22.04 + Python 3.10（不需要 CUDA）
类型：CPU 实例，核数越多越好（脚本会按核数自适应线程）
```

## C2. 拉代码

```bash
cd /root/autodl-tmp
git clone https://github.com/yu2486789817/PE_AI.git   # 已存在则 cd 进去 git pull
cd PE_AI
```

## C3. 上传模型（必须手动，不在 git 里）

只需上传**一个目录**到下面的位置（约 2GB）：

```text
Code/AIChat/models/qwen2.5-pe-sports.q4_k_m/
  ├── qwen2.5-pe-sports.q4_k_m.gguf
  └── Modelfile
```

- 微调原始权重 `Code/AIChat/models/Qwen2.5-3B-PE-Sports/`（safetensors）**不用传**，Ollama 只吃 GGUF。
- 上传方式：AutoDL 的 JupyterLab 拖拽，或用实例给的 SSH 端口 `scp`。

## C4. 启动服务（CPU 版）

```bash
chmod +x Code/deploy/autodl/*.sh
bash Code/deploy/autodl/start_ai_services_cpu.sh
```

与 GPU 脚本的差异：安装 CPU 版 PyTorch、放开线程数（默认 `nproc`）、传入 YOLO 推理调优参数。
可按需覆盖性能参数：

```bash
INFER_IMGSZ=256 PROCESS_SKIP_FACTOR=4 bash Code/deploy/autodl/start_ai_services_cpu.sh
```

确认线程已放开（应接近核数而非 2）：

```bash
source /root/autodl-tmp/PE_AI/.venv-ai/bin/activate
python -c "import torch; print(torch.get_num_threads())"
```

## C5. 公网访问（cloudflared 隧道，无需 VPS）

AutoDL 不直接给干净的公网端口，用 cloudflared 快速隧道（免费、自带 HTTPS）：

```bash
bash Code/deploy/autodl/start_tunnels_cloudflared.sh
```

脚本会为 Yolo(8000) 和 AIChat(5000) 各开一个隧道，并打印两个公网地址：

```text
YOLO_BASE_URL   = https://xxxx.trycloudflare.com
AICHAT_BASE_URL = https://yyyy.trycloudflare.com
```

把这两个地址填到 Render 后端环境变量，保存后 Manual Deploy。

> 注意：trycloudflare 地址在隧道重启后会变化，变了需同步更新 Render 环境变量。

## C6. 健康检查 / 停止

```bash
bash Code/deploy/autodl/health_ai_services.sh
bash Code/deploy/autodl/stop_ai_services.sh   # 同时会停掉 cloudflared 隧道
```

## C7. 性能预期与调优

- 单帧推理耗时看日志（每 10 帧打印一次「帧 X 处理时间」）。
- 嫌慢的调优顺序：先确认线程已放开 → 调小 `INFER_IMGSZ`（320→256）→ 调大 `PROCESS_SKIP_FACTOR`（3→4/5）。
- 聊天为 CPU 逐 token 生成，单次问答几秒~十几秒属正常，演示够用。
