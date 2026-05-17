FaceAuthApp – Missing Person Identification System
📌 Overview

FaceAuthApp is a web-based face recognition system designed to identify missing persons or verify identities using facial features. The application leverages deep learning models to compare facial embeddings and provides accurate matching results.

This system can be used by organizations, institutions, or authorities to efficiently manage and verify identities.

🎯 Features
🔍 Face Registration (Store user face data)
🧠 Face Recognition using Deep Learning
📂 Image Upload & Processing
⚡ Real-time Face Verification
🗄️ SQLite Database Integration
🌐 REST API-based Backend (Flask)
📁 Organized Image Storage System
🧹 Automatic Cleanup for Invalid Records
🛠️ Tech Stack
Backend:
       Python
       Flask
       SQLite
AI/ML:
      DeepFace (Face Recognition)
       PIL (Image Processing)
Others:
       Flask-CORS

📂 Project Structure
FaceAuthApp/
│── app.py                # Main Flask application
│── db_setup.py          # Database initialization
│── database/            # SQLite database
│── static/
│   ├── uploads/         # Registered user images
│   ├── verify_temp/     # Temporary verification images
│   └── tmp/             # Temporary processing folder
│── render.yaml          # Deployment config
│── Procfile.txt         # Deployment process file

⚙️ Installation & Setup
1️⃣ Clone the Repository
cd FaceAuthApp
2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Run the Application
python app.py

Server will start at:

http://127.0.0.1:5000/
🧠 How It Works
User uploads an image for registration.
Image is processed and stored in the database.
During verification:
Uploaded image is compared with stored images
DeepFace extracts embeddings
Similarity is calculated
Best match is returned as result.
📡 API Endpoints (Example)
➤ Register User
POST /register
➤ Verify Face
POST /verify
➤ Get Users
GET /users
🚀 Deployment

This project supports deployment on platforms like:

Render
Railway
AWS (EC2)

Use:

render.yaml
Procfile.txt
⚠️ Limitations
Performance depends on image quality
Works best with clear, front-facing images
Not optimized for very large datasets yet
🔮 Future Improvements
🔐 Admin Dashboard
☁️ Cloud Database Integration (Firebase / MongoDB)
📊 Analytics Dashboard
📱 Mobile App Integration
⚡ Faster Face Matching (Vector DB)


👨‍💻 Author

Aman Raj
