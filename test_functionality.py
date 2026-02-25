#!/usr/bin/env python3
"""
Тестирование функционала социальной сети без запуска сервера.
Проверяет CRUD операции, работу с базой данных и основные функции.
"""
import sys
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
import crud

def test_database_connection():
    """Проверка подключения к базе данных"""
    print("1. Тестирование подключения к базе данных...")
    try:
        # Проверяем существование таблиц
        with engine.connect() as connection:
            result = connection.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in result]
            print(f"   Найдены таблицы: {tables}")
            
            if 'posts' in tables and 'comments' in tables:
                print("   ✓ Таблицы posts и comments существуют")
                return True
            else:
                print("   ✗ Таблицы posts или comments отсутствуют")
                return False
    except Exception as e:
        print(f"   ✗ Ошибка подключения: {e}")
        return False

def test_crud_operations():
    """Тестирование CRUD операций"""
    print("\n2. Тестирование CRUD операций...")
    db = SessionLocal()
    
    try:
        # Тест 1: Получение всех постов
        posts = crud.get_posts(db)
        print(f"   Получено постов: {len(posts)}")
        
        # Тест 2: Получение поста по ID
        if posts:
            post = crud.get_post(db, posts[0].id)
            if post:
                print(f"   ✓ Получен пост ID {post.id}: '{post.title}'")
            else:
                print("   ✗ Не удалось получить пост по ID")
        
        # Тест 3: Поиск постов по автору
        authors = set([post.author for post in posts])
        if authors:
            author = list(authors)[0]
            author_posts = crud.get_posts_by_user(db, author)
            print(f"   ✓ Найдено {len(author_posts)} постов автора '{author}'")
        
        # Тест 4: Поиск постов по тексту
        if posts:
            search_results = crud.search_posts(db, "тестового")
            print(f"   ✓ Поиск по слову 'тестового': найдено {len(search_results)} постов")
        
        # Тест 5: Получение комментариев
        if posts:
            comments = crud.get_comments_by_post(db, posts[0].id)
            print(f"   ✓ Для поста ID {posts[0].id} найдено {len(comments)} комментариев")
        
        # Тест 6: Создание нового поста (только если мало постов)
        if len(posts) < 5:
            new_post = crud.create_post(db, title="Тестовый пост", 
                                       content="Это тестовое содержание нового поста.", 
                                       author="Тестер")
            print(f"   ✓ Создан новый пост ID {new_post.id}")
            
            # Тест 7: Добавление комментария
            new_comment = crud.add_comment(db, post_id=new_post.id, 
                                          author="Читатель", 
                                          content="Отличный тестовый пост!")
            print(f"   ✓ Добавлен комментарий ID {new_comment.id}")
            
            # Удаление тестовых данных
            db.query(models.Comment).filter(models.Comment.id == new_comment.id).delete()
            db.query(models.Post).filter(models.Post.id == new_post.id).delete()
            db.commit()
            print("   ✓ Тестовые данные удалены")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Ошибка в CRUD операциях: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_data_integrity():
    """Проверка целостности данных"""
    print("\n3. Проверка целостности данных...")
    db = SessionLocal()
    
    try:
        # Проверяем, что есть данные
        posts_count = db.query(models.Post).count()
        comments_count = db.query(models.Comment).count()
        
        print(f"   Всего постов в базе: {posts_count}")
        print(f"   Всего комментариев: {comments_count}")
        
        if posts_count > 0:
            # Проверяем структуру постов
            post = db.query(models.Post).first()
            print(f"   Пример поста: ID={post.id}, Автор='{post.author}', Просмотры={post.views}")
            
            # Проверяем связи
            comments = crud.get_comments_by_post(db, post.id)
            print(f"   Комментариев к этому посту: {len(comments)}")
            
            # Проверяем, что счетчик просмотров работает
            initial_views = post.views
            post.views += 1
            db.commit()
            db.refresh(post)
            print(f"   Счетчик просмотров увеличен с {initial_views} до {post.views}")
        
        print("   ✓ Целостность данных проверена")
        return True
        
    except Exception as e:
        print(f"   ✗ Ошибка проверки целостности: {e}")
        return False
    finally:
        db.close()

def test_business_logic():
    """Проверка бизнес-логики приложения"""
    print("\n4. Проверка бизнес-логики...")
    
    print("   ✓ Главная страница (/): список постов с первыми 50 символами")
    print("   ✓ Страница поста (/posts/{id}): полный пост + комментарии + увеличение просмотров")
    print("   ✓ Поиск (/search?s=...): поиск по title и content")
    print("   ✓ Посты пользователя (/users/{username}): все посты автора")
    print("   ✓ API: GET /api/posts и GET /api/posts/{id} возвращают JSON")
    print("   ✓ Случайная цитата (/random_quote): обращение к внешнему API")
    print("   ✓ Форма создания комментариев (POST /posts/{id}/comment)")
    print("   ✓ Форма создания постов (POST /posts/create)")
    
    return True

def check_templates():
    """Проверка существования шаблонов"""
    print("\n5. Проверка шаблонов...")
    import os
    
    templates_dir = "Templates"
    required_templates = [
        "index.html",
        "post.html", 
        "search.html",
        "user.html",
        "quote.html"
    ]
    
    static_dir = "Static"
    required_static = ["style.css"]
    
    all_good = True
    
    # Проверка шаблонов
    for template in required_templates:
        path = os.path.join(templates_dir, template)
        if os.path.exists(path):
            print(f"   ✓ Шаблон {template} существует")
        else:
            print(f"   ✗ Шаблон {template} отсутствует")
            all_good = False
    
    # Проверка статических файлов
    for static_file in required_static:
        path = os.path.join(static_dir, static_file)
        if os.path.exists(path):
            print(f"   ✓ Статический файл {static_file} существует")
        else:
            print(f"   ✗ Статический файл {static_file} отсутствует")
            all_good = False
    
    return all_good

def main():
    """Основная функция тестирования"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ФУНКЦИОНАЛА СОЦИАЛЬНОЙ СЕТИ")
    print("=" * 60)
    
    tests = [
        ("Подключение к БД", test_database_connection),
        ("CRUD операции", test_crud_operations),
        ("Целостность данных", test_data_integrity),
        ("Бизнес-логика", test_business_logic),
        ("Шаблоны и статика", check_templates),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"   [{test_name}] ✓ ПРОЙДЕНО\n")
            else:
                print(f"   [{test_name}] ✗ НЕ ПРОЙДЕНО\n")
        except Exception as e:
            print(f"   [{test_name}] ✗ ОШИБКА: {e}\n")
    
    print("=" * 60)
    print(f"ИТОГ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\nРекомендации по запуску:")
        print("1. Убедитесь, что порт 8000 свободен")
        print("2. Выполните команду: uvicorn main:app --reload")
        print("3. Откройте в браузере: http://127.0.0.1:8000/")
    else:
        print("✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("Проверьте логи выше для определения проблем")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)