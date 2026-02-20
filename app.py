from flask import Flask, render_template, request, redirect, url_for
from models import db, Post
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
import os

# ... весь остальной код выше ...

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///database.db",  # на случай локального запуска без переменной
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True
}  # опционально, но полезно для стабильности
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SECRET_KEY"] = "super-secret-key-123"  # для формы, пока не важно

db.init_app(app)

# Создаём базу данных один раз
with app.app_context():
    db.create_all()


@app.route("/")
def index():
    sort = request.args.get("sort", "new")
    if sort == "likes":
        posts = Post.query.order_by(Post.likes.desc()).all()
    else:
        posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("index.html", posts=posts)


@app.route("/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        image_path = None

        # Отладка: смотри в терминале / логах Render
        print("Полученные файлы:", request.files)
        print("Полученные поля формы:", request.form)

        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename:  # ← проверка на наличие и непустое имя
                filename = secure_filename(file.filename)
                upload_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                try:
                    file.save(upload_path)
                    image_path = filename
                    print(f"Файл успешно сохранён: {upload_path}")
                except Exception as e:
                    print(f"Ошибка сохранения файла: {e}")
                    # Можно добавить flash-сообщение пользователю, но пока просто лог
            else:
                print("Файл не выбран или пустой filename")

        # Создаём пост даже если картинки нет
        new_post = Post(title=title, content=content, image_path=image_path)
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("new_post.html")


@app.route("/post/<int:id>", methods=["GET", "POST"])
def post(id):
    post = Post.query.get_or_404(id)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "like":
            post.likes += 1
        elif action == "comment":
            post.comments += 1
        db.session.commit()
    return render_template("post.html", post=post)


from flask import send_from_directory


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render передаст свой порт
    app.run(debug=True, host="0.0.0.0", port=port)
