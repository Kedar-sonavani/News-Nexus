import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

# User Interaction model
class UserInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Keep track of when the interaction was created

# Function to add a user's interaction to the database
def add_interaction(user_id, article_title, category, description):
    interaction = UserInteraction(user_id=user_id, article_title=article_title,
                                  category=category, description=description)
    db.session.add(interaction)
    db.session.commit()
    print(f"Interaction tracked for user_id={user_id}: {article_title}")

# Function to build and return personalized recommendations for a user
def build_model(user_id):
    # Filter interactions for the specific user
    user_data = UserInteraction.query.filter_by(user_id=user_id).all()

    if not user_data:
        print(f"No interactions found for user_id={user_id}")
        return []

    print(f"Generating recommendations for user_id={user_id}")

    # Convert interactions to a DataFrame
    user_data_df = pd.DataFrame([(interaction.article_title, interaction.category, interaction.description, interaction.rating)
                                  for interaction in user_data], 
                                 columns=['article_title', 'category', 'description', 'rating'])

    # Filter out disliked articles (assuming 0 is dislike)
    user_data_df = user_data_df[user_data_df['rating'] != 0]

    # Use TF-IDF to create article similarity
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(user_data_df['description'])

    # Compute cosine similarity matrix for articles the user interacted with
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    # Create a list to hold recommendations
    recommendations = []

    # Get unique categories of articles the user has liked
    liked_categories = user_data_df[user_data_df['rating'] > 0]['category'].unique()

    # Find similar articles while ensuring diversity
    for i, row in enumerate(user_data_df.iterrows()):
        similar_indices = cosine_sim[i].argsort().flatten()[::-1]
        for idx in similar_indices:
            if idx < len(user_data_df):
                title = user_data_df.iloc[idx]['article_title']
                category = user_data_df.iloc[idx]['category']
                if category not in liked_categories and (title, category) not in recommendations:
                    recommendations.append((title, category))
                if len(recommendations) >= 5:
                    break
        if len(recommendations) >= 5:
            break

    # Return top 5 diverse recommendations
    return recommendations[:5]
