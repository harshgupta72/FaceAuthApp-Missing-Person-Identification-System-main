from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from deepface import DeepFace
from werkzeug.utils import secure_filename
from PIL import Image
import warnings

app = Flask(__name__)
CORS(app)

# 📂 Ensure folders exist
UPLOAD_FOLDER = "static/uploads"
DB_FOLDER = "database"

UPLOAD_FOLDER = "static/uploads"
VERIFY_TEMP_FOLDER = "static/verify_temp"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VERIFY_TEMP_FOLDER, exist_ok=True)




# temporary folder for verification uploads (not persisted)
TMP_UPLOAD_DIR = "static/tmp"
os.makedirs(TMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(DB_FOLDER, exist_ok=True)

DB_PATH = os.path.join(DB_FOLDER, "users.db")

# 🚀 Ignore ICC profile warnings
warnings.filterwarnings("ignore", category=UserWarning, module="PIL.PngImagePlugin")

# 🔹 Helper: Resize and strip ICC
def resize_image(path, max_size=600):
    try:
        img = Image.open(path)
        img.thumbnail((max_size, max_size))
        img.save(path, icc_profile=None)  # strip ICC profile
    except Exception as e:
        print(f"[WARN] resize_image failed: {e}")

# 🔹 Cleanup DB (fix slashes, remove missing files)
def cleanup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, image_path, rel_path FROM users")
    users = cursor.fetchall()

    fixed, removed = 0, 0
    for user_id, name, path, rel in users:
        if not path:
            continue

        new_path = path.replace("\\", "/")
        new_rel = rel.replace("\\", "/") if rel else ""

        if not os.path.exists(new_path):
            print(f"❌ Removing {name} (missing file: {new_path})")
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            removed += 1
            continue

        if new_path != path or new_rel != rel:
            print(f"🔧 Fixing path for {name}: {path} → {new_path}")
            cursor.execute(
                "UPDATE users SET image_path = ?, rel_path = ? WHERE id = ?",
                (new_path, new_rel, user_id),
            )
            fixed += 1

    conn.commit()
    conn.close()
    if fixed or removed:
        print(f"✅ DB Cleanup done → Fixed: {fixed}, Removed: {removed}")

# ✅ Preload DeepFace model
print("🔄 Loading DeepFace model (SFace)...")
MODEL_NAME = "SFace"
model = DeepFace.build_model(MODEL_NAME)
print("✅ Model loaded and ready!")

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "message": "Backend is working!"})

from datetime import datetime

@app.route("/register", methods=["POST"])
def register():
    if "image" not in request.files or "name" not in request.form:
        return jsonify({"status": "error", "message": "Name, image, age, and location required"}), 400

    name = request.form.get("name")
    age = request.form.get("age") or 0   # default 0 if not provided
    location = request.form.get("location") or "Unknown"
    reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # auto timestamp
    image = request.files["image"]

    filename = secure_filename(image.filename)
    rel_path = os.path.join(UPLOAD_FOLDER, filename)
    abs_path = os.path.abspath(rel_path)
    # ✅ Open uploaded image, resize before saving
    img = Image.open(image)
    img.thumbnail((400, 400))   # shrink to max 400x400
    img.save(abs_path, icc_profile=None)


    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            location TEXT,
            reg_date TEXT,
            image_path TEXT,
            rel_path TEXT
        )
    """)

    cursor.execute(
        "INSERT INTO users (name, age, location, reg_date, image_path, rel_path) VALUES (?, ?, ?, ?, ?, ?)",
        (name, age, location, reg_date, abs_path, rel_path)
    )
    conn.commit()
    conn.close()

    cleanup_db()

    return jsonify({
        "status": "success",
        "message": f"User {name} registered!",
        "data": {
            "name": name,
            "age": age,
            "location": location,
            "reg_date": reg_date,
            "image_url": f"http://{request.host}/{rel_path}"
        }
    })

@app.route("/verify", methods=["POST"])
def verify():
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "Image required"}), 400

    image = request.files["image"]
    filename = secure_filename(image.filename)
    rel_path = os.path.join(VERIFY_TEMP_FOLDER, filename)  # save in temp folder
    abs_path = os.path.abspath(rel_path)

    # ✅ Open uploaded image, resize before saving
    img = Image.open(image)
    img.thumbnail((400, 400))   # shrink to max 400x400
    img.save(abs_path, icc_profile=None)


    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, age, location, reg_date, image_path, rel_path FROM users")
    users = cursor.fetchall()
    conn.close()

    best_match = None
    best_confidence = 0.0

    for user in users:
        user_id, db_name, db_age, db_location, db_reg_date, db_abs_path, db_rel_path = user
        try:
            result = DeepFace.verify(
                img1_path=abs_path,
                img2_path=db_abs_path,
                model_name=MODEL_NAME,
                enforce_detection=False
            )

            if result["verified"]:
                distance = result.get("distance", 0.0)
                confidence = round((1 - distance) * 100, 2)

                # always keep highest confidence match
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = {
                        "name": db_name,
                        "age": db_age,
                        "location": db_location,
                        "reg_date": db_reg_date,
                        "registered_image_url": f"http://{request.host}/{db_rel_path}"
                    }

        except Exception as e:
            print("⚠️ DeepFace error:", str(e), "for user:", db_name, "path:", db_abs_path)
            continue

    if best_match:
        return jsonify({
            "status": "success",
            "match": True,
            "confidence": best_confidence,
            "user": best_match,
            "uploaded_image_url": f"http://{request.host}/{rel_path}"
        })

    # ❌ No match case → still return uploaded image URL
    return jsonify({
        "status": "success",
        "match": False,
        "message": "No match found. Please register the person.",
        "uploaded_image_url": f"http://{request.host}/{rel_path}"
    })

@app.route("/cleanup_verify", methods=["POST"])
def cleanup_verify():
    try:
        deleted_files = []
        for f in os.listdir(VERIFY_TEMP_FOLDER):
            file_path = os.path.join(VERIFY_TEMP_FOLDER, f)
            os.remove(file_path)
            deleted_files.append(f)

        return jsonify({
            "status": "success",
            "message": f"Deleted {len(deleted_files)} temp verify images",
            "files": deleted_files
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})



@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Backend is running"})

@app.route("/", methods=["GET"])
def home():
    return """
    <html>
        <head><title>FaceAuth API</title></head>
        <body style="font-family: Arial; text-align: center; margin-top: 100px;">
            <h1>🚀 FaceAuth API is Running!</h1>
            <p>Available Endpoints:</p>
            <ul style="list-style:none;">
                <li>🔹 <a href="/ping">/ping</a></li>
                <li>🔹 <a href="/health">/health</a></li>
                <li>🔹 <b>POST</b> /register</li>
                <li>🔹 <b>POST</b> /verify</li>
            </ul>
        </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
