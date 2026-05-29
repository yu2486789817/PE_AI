# Render + Supabase 免费部署说明

## 1. 创建 Supabase 免费数据库

1. 打开 Supabase，新建一个 Free 项目。
2. 进入 SQL Editor，执行：
   `Code/PE-AI-Backend/src/main/resources/init_supabase.sql`
3. 进入 Project Settings -> Database -> Connection string。
4. 推荐选择 Session pooler 连接串，因为它支持 IPv4，更适合 Render。

Spring Boot 需要 JDBC URL，填到 Render 时要改成这种格式：

```text
jdbc:postgresql://<supabase-pooler-host>:5432/postgres?sslmode=require
```

如果 Supabase 给你的原始连接串是：

```text
postgresql://postgres.<project-ref>:<password>@<host>:5432/postgres
```

就把前缀改成 `jdbc:postgresql://`，并保留 host、端口、数据库名，最后加 `?sslmode=require`。

## 2. 部署 Spring Boot 到 Render

项目根目录已经有 `render.yaml`，后端目录已经有 `Code/PE-AI-Backend/Dockerfile`。

Render 创建 Blueprint 或 Web Service 时，关键配置如下：

```text
Root Directory: Code/PE-AI-Backend
Runtime: Docker
Plan: Free
Health Check Path: /health
```

环境变量：

```text
SPRING_PROFILES_ACTIVE=prod
DATABASE_URL=jdbc:postgresql://<supabase-pooler-host>:5432/postgres?sslmode=require
DATABASE_USERNAME=postgres.<project-ref>
DATABASE_PASSWORD=<你的 Supabase 数据库密码>
JWT_SECRET=<任意长随机字符串>
```

`YOLO_BASE_URL` 和 `AICHAT_BASE_URL` 可以先不改。免费部署阶段先保证登录、课程、作业等数据库功能跑通；视频 AI 和聊天服务后面如果也要公网化，再分别部署。

## 3. 小程序切到 Render 域名

Render 部署成功后，会得到类似下面的 HTTPS 地址：

```text
https://pe-ai-backend.onrender.com
```

把它填到：

```text
Code/PE_AI_Student_UniApp/src/services/request.js
```

修改这一行：

```js
const CLOUD_HOST = 'https://pe-ai-backend.onrender.com';
```

真机调试和上线时都用 HTTPS 域名，不再依赖本机 IP。

## 4. 微信小程序域名配置

在微信公众平台后台，把 Render 域名加入：

```text
开发管理 -> 开发设置 -> 服务器域名 -> request 合法域名
```

开发者工具临时调试可以勾选“不校验合法域名”，但真机正式体验必须配置合法 HTTPS 域名。

## 5. 免费方案限制

Render Free Web Service 空闲后会休眠，第一次访问会慢一些。Supabase Free 项目也有容量和长时间不活跃暂停限制，所以课程演示够用，但不适合作为长期生产环境。

## 6. 教学视频持久化（Supabase Storage）

Render Free 容器磁盘是临时的，重启/重新部署后上传的视频会丢失（表现为"过一会儿视频看不了"）。因此教学视频改用 Supabase Storage 持久化。

### 6.1 在 Supabase 创建 Storage Bucket

1. 进入 Supabase 项目 -> Storage -> New bucket。
2. 名称填 `teaching-videos`，并勾选 **Public bucket**（公开，便于前端直接播放与生成封面）。
3. 创建后即可。

### 6.2 获取 service_role 密钥

1. Project Settings -> API。
2. 复制 `Project URL`（形如 `https://<project-ref>.supabase.co`）。
3. 复制 `service_role` 密钥（一长串 `eyJ...` 的 JWT）。
   - 注意：`service_role` 拥有完全权限，**只能放在后端环境变量**，绝不能出现在前端代码或提交到 git。

### 6.3 在 Render 后台填写环境变量

在后端服务的 Environment 中新增：

```text
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_KEY=<service_role 密钥>
SUPABASE_BUCKET=teaching-videos
```

填好保存后 Render 会自动重新部署。之后：
- 上传视频会存到 Supabase Storage，返回的是 Supabase 公共 URL，持久不丢失。
- 旧的 `/Teaching-video/files/{filename}` 链接会自动 302 重定向到 Supabase 公共 URL，老数据仍可访问（前提是文件已在 Supabase 中）。
- 未配置这三个变量时，后端回退到本地磁盘存储（仅适合本地开发）。

### 6.4 免费额度提醒

Supabase Free 的 Storage 约 1 GB 容量、约 5 GB/月 出站流量。教学视频体积较大，演示时注意控制数量和清晰度；超出需升级到 Pro。
