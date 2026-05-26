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
