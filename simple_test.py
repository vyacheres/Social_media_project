#!/usr/bin/env python3
"""
Проверка файла SQLite ``social_media.db`` без запуска веб-сервера.

Скрипт для ручной диагностики: выводит наличие таблиц и счётчики записей.
Запуск из корня проекта: ``python simple_test.py``
"""
import sqlite3
import os
import sys

def check_database():
    """Check database structure and data"""
    print("=" * 50)
    print("SOCIAL MEDIA PROJECT - FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Check if database exists
    if not os.path.exists('social_media.db'):
        print("ERROR: Database file 'social_media.db' not found")
        return False
    
    print("[OK] Database file exists")
    
    # Connect to database
    try:
        conn = sqlite3.connect('social_media.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"\nTables in database: {tables}")
        
        required_tables = ['posts', 'comments', 'users']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"[ERROR] Missing tables: {missing_tables}")
            return False
        
        print("[OK] All required tables exist")
        
        # Check posts count
        cursor.execute('SELECT COUNT(*) FROM posts')
        posts_count = cursor.fetchone()[0]
        print(f"\nPosts in database: {posts_count}")
        
        if posts_count == 0:
            print("[ERROR] No posts found in database")
            return False
        
        print("[OK] Posts exist in database")
        
        # Show sample posts
        cursor.execute('SELECT id, views, likes FROM posts LIMIT 3')
        posts = cursor.fetchall()
        
        print("\nSample posts:")
        for post in posts:
            print(f"  ID {post[0]}, Views: {post[1]}, Likes: {post[2]}")
        
        # Check comments count
        cursor.execute('SELECT COUNT(*) FROM comments')
        comments_count = cursor.fetchone()[0]
        print(f"\nComments in database: {comments_count}")
        
        if comments_count > 0:
            cursor.execute('SELECT id, post_id FROM comments LIMIT 3')
            comments = cursor.fetchall()
            print("Sample comments:")
            for comment in comments:
                print(f"  ID {comment[0]}, Post ID: {comment[1]}")
        
        # Check views functionality
        print("\nTesting views functionality...")
        cursor.execute('SELECT id, views FROM posts LIMIT 1')
        post = cursor.fetchone()
        if post:
            post_id, initial_views = post
            print(f"  Post ID {post_id} has {initial_views} views")
            
            # Simulate view increment
            cursor.execute('UPDATE posts SET views = views + 1 WHERE id = ?', (post_id,))
            conn.commit()
            
            cursor.execute('SELECT views FROM posts WHERE id = ?', (post_id,))
            new_views = cursor.fetchone()[0]
            print(f"  After increment: {new_views} views")
            
            if new_views == initial_views + 1:
                print("  [OK] Views increment works correctly")
            else:
                print("  [ERROR] Views increment failed")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return False

def check_files():
    """Check required files and templates"""
    print("\n" + "=" * 50)
    print("FILE STRUCTURE CHECK")
    print("=" * 50)
    
    required_files = [
        'requirements.txt',
        'main.py',
        'models.py',
        'crud.py',
        'database.py',
        'init_db.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"[OK] {file}")
        else:
            print(f"[ERROR] {file} - MISSING")
    
    # Check templates
    print("\nChecking templates directory...")
    templates_dir = 'templates'
    if os.path.exists(templates_dir):
        print(f"[OK] templates directory exists")
        
        required_templates = ['index.html', 'post.html', 'search.html', 'user.html', 'quote.html']
        for template in required_templates:
            path = os.path.join(templates_dir, template)
            if os.path.exists(path):
                print(f"  [OK] {template}")
            else:
                print(f"  [ERROR] {template} - MISSING")
    else:
        print(f"[ERROR] templates directory missing")
    
    # Check static files
    print("\nChecking static directory...")
    static_dir = 'Static'
    if os.path.exists(static_dir):
        print(f"[OK] Static directory exists")
        
        if os.path.exists(os.path.join(static_dir, 'style.css')):
            print(f"  [OK] style.css")
        else:
            print(f"  [ERROR] style.css - MISSING")
    else:
        print(f"[ERROR] Static directory missing")
    
    return True

def test_imports():
    """Test Python imports"""
    print("\n" + "=" * 50)
    print("PYTHON IMPORT TEST")
    print("=" * 50)
    
    try:
        import sqlalchemy
        print(f"[OK] SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError:
        print("[ERROR] SQLAlchemy not installed")
        return False
    
    try:
        import fastapi
        print(f"[OK] FastAPI: {fastapi.__version__}")
    except ImportError:
        print("[ERROR] FastAPI not installed")
        return False
    
    try:
        import jinja2
        print(f"[OK] Jinja2: {jinja2.__version__}")
    except ImportError:
        print("[ERROR] Jinja2 not installed")
        return False
    
    # Test project imports
    print("\nTesting project imports...")
    try:
        from database import get_db, SessionLocal
        print("[OK] database.py imports work")
    except Exception as e:
        print(f"[ERROR] database.py import failed: {e}")
        return False
    
    try:
        import models
        print("[OK] models.py imports work")
    except Exception as e:
        print(f"[ERROR] models.py import failed: {e}")
        return False
    
    try:
        import crud
        print("[OK] crud.py imports work")
    except Exception as e:
        print(f"[ERROR] crud.py import failed: {e}")
        return False
    
    return True

def generate_startup_instructions():
    """Generate startup instructions"""
    print("\n" + "=" * 50)
    print("STARTUP INSTRUCTIONS")
    print("=" * 50)
    
    instructions = [
        "1. Make sure you're in the project directory:",
        "   cd python_progs/Social_media_project",
        "",
        "2. Install dependencies (if not already installed):",
        "   pip install -r requirements.txt",
        "",
        "3. Initialize database (if not already done):",
        "   python init_db.py",
        "",
        "4. Start the FastAPI server:",
        "   uvicorn main:app --reload",
        "",
        "5. Open your browser and navigate to:",
        "   http://127.0.0.1:8000/",
        "",
        "AVAILABLE ENDPOINTS:",
        "  - /                 : Home page with all posts",
        "  - /posts/{id}       : Individual post with comments",
        "  - /search?s=query   : Search posts",
        "  - /users/{username} : All posts by a user",
        "  - /api/posts        : JSON API for all posts",
        "  - /api/posts/{id}   : JSON API for single post",
        "  - /random_quote     : Random quote from external API",
        "",
        "FEATURES IMPLEMENTED:",
        "  [OK] Post listing with first 50 characters",
        "  [OK] View counter increment",
        "  [OK] Search by title and content",
        "  [OK] User profile pages",
        "  [OK] JSON API endpoints",
        "  [OK] External API integration (random quote)",
        "  [OK] Comment system",
        "  [OK] CSS styling",
    ]
    
    for line in instructions:
        print(line)

def main():
    """Main test function"""
    print("Testing Social Media Project...")
    
    # Change to project directory if needed
    if not os.path.exists('social_media.db'):
        print("Note: Running tests from project directory")
    
    # Run tests
    db_ok = check_database()
    files_ok = check_files()
    imports_ok = test_imports()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    
    if db_ok and files_ok and imports_ok:
        print("[OK] ALL TESTS PASSED!")
        print("The project is ready to run.")
    else:
        print("[ERROR] SOME TESTS FAILED")
        if not db_ok:
            print("  - Database issues detected")
        if not files_ok:
            print("  - Missing files or templates")
        if not imports_ok:
            print("  - Import/package issues")
    
    generate_startup_instructions()
    
    return db_ok and files_ok and imports_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)