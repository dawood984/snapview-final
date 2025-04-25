# trigger redeployyy

from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.utils import secure_filename
import os
import uuid
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from models.database import (
    init_db, add_user, get_user, add_post, get_all_posts, get_posts_by_user,
    add_comment, get_comments, add_like, count_likes, delete_post
)

# Load .env secrets
load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecretkey'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}

# Azure Blob Storage (loaded from .env)
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = "uploads"
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

# Init DB (commented for deployment safety)
# init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    posts = get_all_posts()
    for post in posts:
        post['likes'] = count_likes(post['id'])
        post['comments'] = get_comments(post['id'])
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        selected_role = request.form['role']

        user = get_user(username)
        if not user:
            flash("Username not found.")
        elif user['password'] != password:
            flash("Incorrect password.")
        elif user['role'] != selected_role:
            flash(f"You are registered as a {user['role'].capitalize()}, not a {selected_role.capitalize()}.")
        else:
            session['username'] = user['username']
            session['role'] = user['role']
            flash("Logged in successfully.")
            return redirect(url_for('creator_dashboard') if user['role'] == 'creator' else url_for('consumer_dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        success = add_user(username, password, role)
        if success:
            flash("Registered successfully. Please log in.")
            return redirect(url_for('login'))
        else:
            flash("Username already exists. Choose another.")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('login'))

@app.route('/creator')
def creator_dashboard():
    if 'username' not in session or session.get('role') != 'creator':
        return redirect(url_for('login'))
    return render_template('creator_dashboard.html')

@app.route('/consumer')
def consumer_dashboard():
    if 'username' not in session or session.get('role') != 'consumer':
        return redirect(url_for('login'))

    posts = get_all_posts()
    for post in posts:
        post['likes'] = count_likes(post['id'])
        post['comments'] = get_comments(post['id'])
    return render_template('consumer_dashboard.html', posts=posts)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session or session.get('role') != 'creator':
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['media']
        title = request.form['title']
        caption = request.form['caption']
        location = request.form['location']
        people = request.form['people']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            blob_client = container_client.get_blob_client(unique_filename)
            blob_client.upload_blob(file, overwrite=True)
            blob_url = f"https://snapviewstore.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{unique_filename}"
            add_post(blob_url, title, caption, location, people, session['username'])
            flash('Upload successful!')
            return redirect(url_for('creator_dashboard'))
        else:
            flash('Invalid file type.')

    return render_template('upload.html')

@app.route('/my_uploads')
def my_uploads():
    if 'username' not in session or session.get('role') != 'creator':
        return redirect(url_for('login'))

    posts = get_posts_by_user(session['username'])
    for post in posts:
        post['likes'] = count_likes(post['id'])
        post['comments'] = get_comments(post['id'])
    return render_template('my_uploads.html', posts=posts)

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if 'username' not in session or session.get('role') != 'creator':
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    success = delete_post(post_id, session['username'])
    flash("Post deleted successfully." if success else "You can only delete your own posts.")
    return redirect(url_for('my_uploads'))

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    if 'username' not in session:
        flash("Login to comment.")
        return redirect(url_for('login'))
    text = request.form.get('comment')
    if text:
        add_comment(post_id, session['username'], text)
    return redirect(request.referrer)

@app.route('/like/<int:post_id>')
def like(post_id):
    if 'username' not in session:
        flash("Login to like posts.")
        return redirect(url_for('login'))
    add_like(post_id, session['username'])
    return redirect(request.referrer)

# Optional: Health check route
@app.route('/ping')
def ping():
    return "App is alive!"

if __name__ == '__main__':
    app.run(debug=True)
