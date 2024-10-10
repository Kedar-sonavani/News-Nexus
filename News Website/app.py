from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)  
    email = db.Column(db.String(150), unique=True, nullable=False)

# In-memory DataFrame to store user interactions
user_interactions = pd.DataFrame(columns=['user_id', 'article_title', 'category', 'description'])

# Function to add a user's interaction to the dataset
def add_interaction(user_id, article_title, category, description):
    global user_interactions
    new_interaction = pd.DataFrame([{
        'user_id': user_id,
        'article_title': article_title,
        'category': category,
        'description': description
    }])
    user_interactions = pd.concat([user_interactions, new_interaction], ignore_index=True)

# Function to build and return personalized recommendations for a user
def build_model(user_id):
    user_data = user_interactions[user_interactions['user_id'] == user_id]
    
    if user_data.empty:
        return []

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(user_data['description'])
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
    
    similar_indices = cosine_sim.argsort().flatten()[::-1]
    similar_items = [(user_data.iloc[i]['article_title'], user_data.iloc[i]['category']) 
                     for i in similar_indices if i < len(user_data)]
    
    return similar_items[:5]

@app.route('/')
def home():
    user = request.args.get('user')  
    history = user_interactions[user_interactions['user_id'] == user] if user else pd.DataFrame()
    recommendations = build_model(user) if user else []
    return render_template('index.html', user=user, history=history, recommendations=recommendations)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            return jsonify({"status": "Login successful", "redirect": "/?user=" + username}), 200
        else:
            return jsonify({"status": "Invalid username or password"}), 401
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"status": "Username or email already exists"}), 409
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, email=email)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "Signup successful", "redirect": "/login"}), 201

@app.route('/track', methods=['POST'])
def track_interaction():
    data = request.json
    user_id = data.get('user_id')
    article_title = data.get('title')
    category = data.get('category')
    description = data.get('description')
    
    if not all([user_id, article_title, category, description]):
        return jsonify({"error": "Incomplete data"}), 400
    
    add_interaction(user_id, article_title, category, description)
    return jsonify({"status": "Interaction tracked"}), 200

@app.route('/recommendations')
def recommendations():
    user = request.args.get('user')
    if user:
        history = user_interactions[user_interactions['user_id'] == user]
        recommendations = build_model(user)
    else:
        history = pd.DataFrame()
        recommendations = []

    return render_template('recommendations.html', user=user, history=history, recommendations=recommendations)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database tables
    app.run(debug=True)
