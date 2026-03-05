from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Table, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from datetime import datetime
import math
import hashlib

# ==================== 数据库配置 ====================
DATABASE_URL = "sqlite:///./blog.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== 数据模型 ====================
# 多对多关联表：文章与标签
article_tag_table = Table(
    'article_tag', Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    articles = relationship("Article", back_populates="author")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    articles = relationship("Article", back_populates="category")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    articles = relationship("Article", secondary=article_tag_table, back_populates="tags")


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="draft")  # draft, published
    created_at = Column(DateTime, default=datetime.now)

    author_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))

    author = relationship("User", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    tags = relationship("Tag", secondary=article_tag_table, back_populates="articles")
    comments = relationship("Comment", back_populates="article", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"))
    created_at = Column(DateTime, default=datetime.now)
    is_approved = Column(Boolean, default=False)
    article = relationship("Article", back_populates="comments")


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)


Base.metadata.create_all(bind=engine)

# ==================== 初始化与依赖 ====================
app = FastAPI(title="Blog Admin")
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 密码加密助手
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


# 初始化默认管理员
def init_admin():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        admin = User(username="admin", password_hash=hash_password("admin123"), is_admin=True)
        db.add(admin)
        db.commit()
    db.close()


init_admin()  # 启动时执行


# 身份验证依赖
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    user = db.query(User).filter(User.username == token).first()  # 简单实现，生产环境请用JWT
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user


# ==================== 认证路由 ====================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...),
                db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user and user.password_hash == hash_password(password):
        response = RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_token", value=username, httponly=True)
        return response
    return HTMLResponse("登录失败，<a href='/login'>返回</a>", status_code=400)


@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_token")
    return response


# ==================== 文章管理路由 ====================
@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/articles")


@app.get("/articles", response_class=HTMLResponse)
async def list_articles(request: Request, q: str = "", page: int = 1, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    query = db.query(Article)
    if q:
        query = query.filter(Article.title.contains(q))

    per_page = 5
    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    items = query.order_by(Article.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    categories = db.query(Category).all()
    tags = db.query(Tag).all()

    return templates.TemplateResponse("articles.html", {
        "request": request, "user": user, "items": items, "q": q, "page": page,
        "total_pages": total_pages, "active": "articles",
        "categories": categories, "tags": tags
    })


@app.post("/articles/add")
async def add_article(request: Request, title: str = Form(...), content: str = Form(...), category_id: int = Form(...),
                      article_status: str = Form(...,alias="status"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    form_data = await request.form()
    tag_ids = form_data.getlist("tag_ids")

    new_article = Article(title=title, content=content, category_id=category_id, status=article_status, author_id=user.id)
    if tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_([int(tid) for tid in tag_ids])).all()
        new_article.tags = tags

    db.add(new_article)
    db.commit()
    return RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/articles/delete/{id}")
async def delete_article(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    article = db.query(Article).filter(Article.id == id).first()
    if article:
        db.delete(article)
        db.commit()
    return RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)


# ==================== 分类与标签路由 ====================
@app.get("/taxonomy", response_class=HTMLResponse)
async def list_taxonomy(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    categories = db.query(Category).all()
    tags = db.query(Tag).all()
    return templates.TemplateResponse("taxonomy.html", {
        "request": request, "user": user, "categories": categories, "tags": tags, "active": "taxonomy"
    })


@app.post("/taxonomy/category/add")
async def add_category(name: str = Form(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.add(Category(name=name))
    db.commit()
    return RedirectResponse(url="/taxonomy", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/taxonomy/tag/add")
async def add_tag(name: str = Form(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.add(Tag(name=name))
    db.commit()
    return RedirectResponse(url="/taxonomy", status_code=status.HTTP_303_SEE_OTHER)


# ==================== 初始化默认设置 ====================
def init_settings():
    db = SessionLocal()
    defaults = {
        "blog_title": "我的个人博客",
        "seo_keywords": "FastAPI, 博客, 技术, 随笔",
        "seo_description": "这是一个基于 FastAPI + SQLAlchemy 构建的高性能个人博客系统。",
        "footer_text": "© 2026 My Blog. All rights reserved."
    }
    for k, v in defaults.items():
        if not db.query(Setting).filter(Setting.key == k).first():
            db.add(Setting(key=k, value=v))
    db.commit()
    db.close()


init_settings()  # 启动时初始化设置


# ==================== 评论管理路由 ====================
@app.get("/comments", response_class=HTMLResponse)
async def list_comments(request: Request, page: int = 1, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    per_page = 8
    query = db.query(Comment)
    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    items = query.order_by(Comment.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return templates.TemplateResponse("comments.html", {
        "request": request, "user": user, "items": items, "page": page,
        "total_pages": total_pages, "active": "comments"
    })


@app.post("/comments/toggle_status/{id}")
async def toggle_comment_status(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == id).first()
    if comment:
        comment.is_approved = not comment.is_approved
        db.commit()
    return RedirectResponse(url="/comments", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/comments/delete/{id}")
async def delete_comment(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == id).first()
    if comment:
        db.delete(comment)
        db.commit()
    return RedirectResponse(url="/comments", status_code=status.HTTP_303_SEE_OTHER)


# ==================== 系统设置路由 ====================
@app.get("/settings", response_class=HTMLResponse)
async def view_settings(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 将数据库中的配置转为字典，方便前端渲染
    settings_data = {s.key: s.value for s in db.query(Setting).all()}
    return templates.TemplateResponse("settings.html", {
        "request": request, "user": user, "settings": settings_data, "active": "settings"
    })


@app.post("/settings/update")
async def update_settings(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    form_data = await request.form()
    for key, value in form_data.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            db.add(Setting(key=key, value=value))
    db.commit()
    return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)