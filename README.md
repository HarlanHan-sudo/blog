# 🌟 FastAPI 个人博客后台管理系统 (Blog Admin System)

基于 **Python 3.12 + FastAPI + SQLAlchemy + Jinja2** 构建的高性能、现代化的个人博客后台管理系统。

本项目采用了极简的后端架构搭配**纯本地零依赖**（无外部 CDN）的现代化前端 UI，实现了从文章发布、分类标签管理到评论审核、系统设置的完整闭环，非常适合作为个人博客的强力引擎或全栈学习项目。

---

## ✨ 核心功能模块

本项目包含了完整的内容管理系统（CMS）所必备的核心模块：

- **🔐 身份验证与权限 (User & Auth)**
  - 基于 Cookie 的安全登录/注销机制。
  - 路由级拦截，保护后台接口与页面安全。
  - 密码 SHA-256 加密存储。
- **📝 文章管理 (Article Management)**
  - 支持文章的增删改查（CRUD）。
  - **状态管理**：一键切换“发布 (Published)”与“草稿 (Draft)”。
  - **关联归属**：支持单选分类 (1:N) 与多选标签 (N:M)。
  - 支持按标题关键词进行模糊搜索与服务端分页。
- **🏷️ 分类与标签 (Taxonomy)**
  - 独立的可视化分类与标签管理卡片。
  - 便捷的弹窗新增体验。
- **💬 评论管理 (Comment Management)**
  - 读者评论集中展示。
  - **审核机制**：一键“通过/撤下”评论，防止垃圾留言。
  - 级联删除：文章被删除时，相关评论会自动清理。
- **⚙️ 系统设置 (System Settings)**
  - 全局键值对 (Key-Value) 配置中心。
  - 动态管理博客名称、SEO 关键词、SEO 描述及页脚版权信息，极具扩展性。

---

## 🎨 前端 UI 特性

- **纯本地手写，零外部依赖**：无需引入 Bootstrap、Tailwind 或任何外部 CDN，离线环境完美运行。
- **现代化设计语言**：
  - 运用 **Glassmorphism (毛玻璃)** 效果、平滑渐变背景。
  - 柔和的卡片阴影 (`box-shadow`) 与圆角 (`border-radius`)。
  - 原生 JavaScript 实现的顺滑 Modal (模态框) 交互与状态切换徽章。

---

## 🛠️ 技术栈

### 后端
- **Python 3.12**
- **FastAPI**：现代、极速的异步 Web 框架。
- **SQLAlchemy**：企业级 ORM 库，完美处理各类关系映射。
- **SQLite**：轻量级本地数据库，开箱即用，免配置。

### 前端
- **Jinja2**：强大的 Python 服务端模板引擎。
- **HTML5 / CSS3 / Vanilla JS**：纯原生前端技术栈。

---

## 📂 项目结构

```text
blog_admin/
├── main.py              # 核心业务逻辑 (路由、Auth、数据库模型、依赖注入)
├── blog.db              # SQLite 数据库文件 (首次启动自动生成)
├── README.md            # 项目说明文档
└── templates/           # 页面模板目录
    ├── base.html        # 全局基础框架 (包含侧边栏导航与所有 CSS/JS)
    ├── login.html       # 独立登录页面
    ├── articles.html    # 文章管理视图
    ├── taxonomy.html    # 分类与标签管理视图
    ├── comments.html    # 评论审核视图
    └── settings.html    # 全局系统设置视图
```

## 🏷️ 快速启动
1.确保已正确安装Python3.12。官网链接：https://www.python.org/downloads/release/python-3120/
2.在根目录下安装所需依赖
```text
pip install fastapi uvicorn sqlalchemy jinja2 python-multipart
```
3.运行服务
```text
uvicorn main:app --reload
```
4.成功运行后，点击 http://127.0.0.1:8000 进入后台，系统首次启动时会自动初始化管理员账号与默认设置：
```
用户名：admin
密码：admin123
```
