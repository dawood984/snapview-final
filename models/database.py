import sqlite3

DB_NAME = 'snapview.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Posts table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            title TEXT,
            caption TEXT,
            location TEXT,
            people TEXT,
            posted_by TEXT NOT NULL,
            FOREIGN KEY(posted_by) REFERENCES users(username)
        )
    ''')

    # Comments table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            commenter TEXT NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    ''')

    # Likes table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            liked_by TEXT NOT NULL,
            UNIQUE(post_id, liked_by),
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    ''')

    conn.commit()
    conn.close()

# ==== USERS ====

def add_user(username, password, role):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT username, password, role FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {'username': row[0], 'password': row[1], 'role': row[2]}
    return None

# ==== POSTS ====

def add_post(filename, title, caption, location, people, posted_by):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO posts (filename, title, caption, location, people, posted_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, title, caption, location, people, posted_by))
    conn.commit()
    conn.close()

def get_all_posts():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, filename, title, caption, location, people, posted_by FROM posts ORDER BY id DESC')
    rows = cur.fetchall()
    conn.close()
    return [
        {
            'id': row[0],
            'filename': row[1],
            'title': row[2],
            'caption': row[3],
            'location': row[4],
            'people': row[5],
            'username': row[6]
        } for row in rows
    ]

def get_posts_by_user(username):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, filename, title, caption, location, people FROM posts WHERE posted_by = ? ORDER BY id DESC', (username,))
    rows = cur.fetchall()
    conn.close()
    return [
        {
            'id': row[0],
            'filename': row[1],
            'title': row[2],
            'caption': row[3],
            'location': row[4],
            'people': row[5],
            'username': username
        } for row in rows
    ]

# ==== COMMENTS ====

def add_comment(post_id, commenter, text):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO comments (post_id, commenter, text) VALUES (?, ?, ?)", (post_id, commenter, text))
    conn.commit()
    conn.close()

def get_comments(post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT commenter, text FROM comments WHERE post_id = ? ORDER BY id ASC", (post_id,))
    rows = cur.fetchall()
    conn.close()
    return [{'commenter': row[0], 'text': row[1]} for row in rows]

# ==== LIKES ====

def add_like(post_id, liked_by):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO likes (post_id, liked_by) VALUES (?, ?)", (post_id, liked_by))
        conn.commit()
    finally:
        conn.close()

def count_likes(post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def delete_post(post_id, username):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Ensure only the post owner can delete
    cur.execute("SELECT posted_by FROM posts WHERE id = ?", (post_id,))
    row = cur.fetchone()
    if not row or row[0] != username:
        conn.close()
        return False

    # Delete the post
    cur.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return True
