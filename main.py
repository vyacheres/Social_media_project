# Импорт необходимых классов и функций из библиотек
# FastAPI - веб-фреймворк для создания API
# Request - объект запроса для работы с HTTP-запросами
# Depends - для внедрения зависимостей (например, сессии БД)
# Form - для обработки данных форм
# HTTPException - для генерации HTTP-ошибок
from fastapi import FastAPI, Request, Depends, Form, HTTPException

# Импорт классов для работы с ответами
# HTMLResponse - для возврата HTML-страниц
# StaticFiles - для раздачи статических файлов (CSS, JS, изображения)
# Jinja2Templates - для рендеринга HTML-шаблонов с данными
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Импорт Session из SQLAlchemy для работы с базой данных
from sqlalchemy.orm import Session

# Импорт функций CRUD операций из модуля crud
import crud

# Импорт функции get_db для получения сессии базы данных
from database import get_db

# Импорт httpx для выполнения HTTP-запросов к внешним API
import httpx

# Создание экземпляра приложения FastAPI
# title - название приложения
# description - описание (можно добавить)
app = FastAPI()

# Монтирование директории со статическими файлами по пути /static
# Теперь файлы из папки Static доступны по адресу http://127.0.0.1:8000/static/...
app.mount("/static", StaticFiles(directory="Static"), name="static")

# Настройка шаблонизатора Jinja2
# Указываем директорию с HTML-шаблонами
templates = Jinja2Templates(directory="Templates")


# Маршрут главной страницы - отображает список всех постов
# @app.get("/") - декоратор, обрабатывающий GET-запросы на корень сайта
# response_class=HTMLResponse - указывает, что возвращается HTML
# async def - асинхронная функция
# request: Request - объект HTTP-запроса (обязателен для шаблонов)
# db: Session = Depends(get_db) - внедрение сессии БД через зависимость
@app.get("/", response_class=HTMLResponse)
async def read_posts(request: Request, db: Session = Depends(get_db)):
    # Получение всех постов из базы данных через CRUD
    posts = crud.get_posts(db)

    # Рендеринг шаблона index.html с передачей данных
    # templates.TemplateResponse - метод для рендеринга шаблона
    # {"request": request, "posts": posts} - словарь с данными для шаблона
    return templates.TemplateResponse(
        "index.html", {"request": request, "posts": posts}
    )


# Маршрут просмотра отдельного поста
# {post_id} - параметр URL, который передается в функцию
@app.get("/posts/{post_id}", response_class=HTMLResponse)
async def read_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    # Получение поста по ID из базы данных
    post = crud.get_post(db, post_id)

    # Проверка, найден ли пост
    # Если пост не найден - генерируем ошибку 404
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    # Получение комментариев для этого поста
    comments = crud.get_comments_by_post(db, post_id)

    # Увеличение счетчика просмотров на 1
    # post.views += 1 - инкремент поля views
    post.views += 1

    # Сохранение изменений в базе данных
    db.commit()

    # Обновление объекта post данными из БД (для получения актуальных значений)
    db.refresh(post)

    # Рендеринг шаблона post.html с данными поста и комментариев
    return templates.TemplateResponse(
        "post.html", {"request": request, "post": post, "comments": comments}
    )


# Маршрут поиска постов
# s - параметр запроса (query parameter), например: /search?s=текст
@app.get("/search", response_class=HTMLResponse)
async def search_posts(request: Request, s: str = "", db: Session = Depends(get_db)):
    # Пустой список для результатов поиска
    results = []

    # Проверка, что поисковый запрос не пустой
    # .strip() удаляет пробелы в начале и конце строки
    if s.strip():
        # Выполнение поиска через CRUD
        # Функция ищет по заголовку и содержимому поста
        results = crud.search_posts(db, s.strip())

    # Рендеринг шаблона search.html с результатами и исходным запросом
    return templates.TemplateResponse(
        "search.html", {"request": request, "posts": results, "query": s}
    )


# Маршрут страницы пользователя
# {username} - имя пользователя в URL
@app.get("/users/{username}", response_class=HTMLResponse)
async def user_posts(request: Request, username: str, db: Session = Depends(get_db)):
    # Получение всех постов конкретного автора
    posts = crud.get_posts_by_user(db, username)

    # Рендеринг шаблона user.html с постами и именем пользователя
    return templates.TemplateResponse(
        "user.html", {"request": request, "posts": posts, "username": username}
    )


# API маршрут для получения списка постов в формате JSON
# Этот маршрут не возвращает HTML, а возвращает данные в JSON формате
@app.get("/api/posts")
async def api_get_posts(db: Session = Depends(get_db)):
    # Получение всех постов из БД
    posts = crud.get_posts(db)

    # Преобразование объектов SQLAlchemy в словари Python
    # Генератор списка - для каждого поста создаем словарь с нужными полями
    return [
        {
            "id": p.id,  # ID поста
            "title": p.title,  # Заголовок поста
            "author": p.author,  # Автор поста
            "content": p.content,  # Содержимое поста
            "views": p.views,  # Количество просмотров
            "likes": p.likes,  # Количество лайков
        }
        for p in posts  # для каждого поста p в списке posts
    ]


# API маршрут для получения одного поста по ID в формате JSON
@app.get("/api/posts/{post_id}")
async def api_get_post(post_id: int, db: Session = Depends(get_db)):
    # Получение поста по ID
    post = crud.get_post(db, post_id)

    # Если пост не найден - ошибка 404
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    # Возврат данных поста в виде словаря (FastAPI автоматически конвертирует в JSON)
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author": post.author,
        "views": post.views,
        "likes": post.likes,
    }


# Маршрут создания нового поста (обработка формы)
# @app.post - декоратор для POST-запросов
# Form(...) - обязательные поля формы
@app.post("/posts/create", response_class=HTMLResponse)
async def create_post(
    request: Request,  # Объект запроса
    title: str = Form(...),  # Заголовок поста из формы
    content: str = Form(...),  # Содержимое поста из формы
    author: str = Form(...),  # Автор поста из формы
    db: Session = Depends(get_db),  # Сессия БД
):
    # Валидация: проверка, что все поля заполнены
    # Если хотя бы одно поле пустое - ошибка 400
    if not title or not content or not author:
        raise HTTPException(status_code=400, detail="Все поля обязательны")

    # Создание нового поста через CRUD
    new_post = crud.create_post(db, title=title, content=content, author=author)

    # Перенаправление на страницу созданного поста
    # Рендерим шаблон post.html с данными нового поста
    return templates.TemplateResponse(
        "post.html", {"request": request, "post": new_post, "comments": []}
    )


# Маршрут добавления комментария к посту
# post_id передается в URL, данные формы - author и content
@app.post("/posts/{post_id}/comment", response_class=HTMLResponse)
async def add_comment(
    request: Request,  # Объект запроса
    post_id: int,  # ID поста из URL
    author: str = Form(...),  # Автор комментария из формы
    content: str = Form(...),  # Содержимое комментария из формы
    db: Session = Depends(get_db),  # Сессия БД
):
    # Проверка существования поста
    post = crud.get_post(db, post_id)
    if not post:
        # Если пост не найден - ошибка 404
        raise HTTPException(status_code=404, detail="Пост не найден")

    # Добавление комментария в базу данных через CRUD
    crud.add_comment(db, post_id=post_id, author=author, content=content)

    # Получение обновленного списка комментариев для поста
    comments = crud.get_comments_by_post(db, post_id)

    # Рендеринг страницы поста с обновленным списком комментариев
    return templates.TemplateResponse(
        "post.html", {"request": request, "post": post, "comments": comments}
    )


# Маршрут для отображения случайной цитаты
# Использует внешнее API (quotable.io) для получения цитаты
@app.get("/random_quote", response_class=HTMLResponse)
async def random_quote(request: Request):
    try:
        # Создание асинхронного HTTP-клиента
        # async with - автоматическое закрытие соединения после использования
        async with httpx.AsyncClient() as client:
            # Выполнение GET-запроса к внешнему API цитат
            # timeout=5.0 - таймаут 5 секунд
            resp = await client.get("https://api.quotable.io/random", timeout=5.0)

            # Проверка успешности ответа (код 200)
            resp.raise_for_status()

            # Парсинг JSON-ответа
            data = resp.json()

            # Извлечение текста цитаты и автора
            # .get() - безопасное получение значения (вернет значение по умолчанию если ключа нет)
            quote_text = data.get("content", "Цитата недоступна")
            quote_author = data.get("author", "Неизвестный")

    except httpx.RequestError:
        # Обработка ошибок сети/запроса
        # Если внешний API недоступен - используем значения по умолчанию
        quote_text = "Цитата недоступна"
        quote_author = "Администрация"

    # Рендеринг шаблона quote.html с данными цитаты
    return templates.TemplateResponse(
        "quote.html", {"request": request, "quote": quote_text, "author": quote_author}
    )


# Точка входа в приложение
# Запускается только если файл запущен напрямую (а не импортирован)
if __name__ == "__main__":
    # Импорт uvicorn внутри блока, чтобы избежать ошибок при импорте
    import uvicorn

    # Запуск сервера uvicorn
    # "main:app" - ссылка на приложение (файл main.py, объект app)
    # host="127.0.0.1" - адрес хоста (localhost)
    # port=8000 - порт сервера
    # reload=True - автоматическая перезагрузка при изменении кода (режим разработки)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
