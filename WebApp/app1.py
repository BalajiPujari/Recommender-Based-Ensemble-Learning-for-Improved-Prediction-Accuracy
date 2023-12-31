# # -*- coding: utf-8 -*-
# """Copy of Ensemble Based Movie Recommendation System.ipynb
#
# Automatically generated by Colaboratory.
#
# Original file is located at
#     https://colab.research.google.com/drive/1ft0W4Fb13Cr6EjvLRTDMQFDvn6Q5YTZw
# """
#
# pip install surprise
#
# pip install streamlit

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from surprise import accuracy
import joblib
import streamlit as st
import requests

df0 = pd.read_csv("./movies0.csv")
df1 = pd.read_csv("./movies1.csv")
df2 = pd.read_csv("./movies2.csv")

users = pd.read_csv('./processed_users.csv')
ratings = pd.read_csv('./processed_ratings.csv')

model = joblib.load('./SVD_model.pkl')

content_based_weight_0 = 2.7888029720654215
content_based_weight_1 = 3.210108934965727
content_based_weight_2 = 3.2979804143559197

collaborative_based_weight_0 = 3.6941800857771883
collaborative_based_weight_1 = 4.323371853783301
collaborative_based_weight_2 = 4.240192342400302

hybrid_model_weight_0 = 3.524485691318226
hybrid_model_weight_1 = 4.359161635313443
hybrid_model_weight_2 = 4.227366515440555

df0_cosine_sim = np.load('./df0_cosine_sim.npy')
df1_cosine_sim = np.load('./df1_cosine_sim.npy')
df2_cosine_sim = np.load('./df2_cosine_sim.npy')

df0_movie_ratings = pd.read_csv('./df0_movie_ratings')
df1_movie_ratings = pd.read_csv('./df1_movie_ratings')
df2_movie_ratings = pd.read_csv('./df2_movie_ratings')

movies = np.load('./movies_titles.npy', allow_pickle=True)

def determine_category(user_favorite_movie, df0, df1, df2):

    # Define the MovieID ranges for each category
    df0_movie_ids = df0['Title'].unique()
    df1_movie_ids = df1['Title'].unique()
    df2_movie_ids = df2['Title'].unique()
    print('Category determined...')
    # Check which category the user's favorite movie falls into
    if user_favorite_movie in df0_movie_ids:
        return 'df0'
    elif user_favorite_movie in df1_movie_ids:
        return 'df1'
    elif user_favorite_movie in df2_movie_ids:
        return 'df2'
    else:
        return 'unknown'  # Handle cases where the category is not recognized

# Define a function to get movie recommendations based on movie title
def get_content_based_recommendations(movies, title, cosine_sim, content_n = 10):
    idx = movies.index[movies['Title'] == title].tolist()[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:content_n+1]  # Top content_n similar movies
    movie_indices = [i[0] for i in sim_scores]
    print('Content based recommendations obtained...')
    return movies['Title'].iloc[movie_indices]

def get_collaborative_recommendations(movies, ratings, user_id, n=10):
    user_ratings = ratings[ratings['User_ID'] == user_id]
    user_unrated_movies = movies[~movies['MovieID'].isin(user_ratings['MovieID'])]
    predictions = []
    for movie_id in user_unrated_movies['MovieID']:
        movie_prediction = model.predict(user_id, movie_id)
        predictions.append((movie_id, movie_prediction.est))
    predictions.sort(key=lambda x: x[1], reverse=True)
    top_predictions = predictions[:n]
    recommended_movie_ids = [x[0] for x in top_predictions]
    print('Collaborative based recommendations obtained...')
    return movies[movies['MovieID'].isin(recommended_movie_ids)]['Title']

def get_hybrid_recommendations(user_favorite_movie, user_id, content_n=5, collaborative_n=5):
    # Determine the category of the user's favorite movie (you need to implement this logic)
    user_favorite_movie_category = determine_category(user_favorite_movie, df0, df1, df2)  # Implement your logic here

    # Based on the category, use the corresponding cosine similarity matrix
    if user_favorite_movie_category == 'df0':
        movies = df0
        cosine_sim = df0_cosine_sim
        df_ratings = df0_movie_ratings
    elif user_favorite_movie_category == 'df1':
        movies = df1
        cosine_sim = df1_cosine_sim
        df_ratings = df1_movie_ratings
    elif user_favorite_movie_category == 'df2':
        movies = df2
        cosine_sim = df2_cosine_sim
        df_ratings = df2_movie_ratings

    # Get content-based and collaborative-based recommendations
    content_recommendations = get_content_based_recommendations(movies, user_favorite_movie, cosine_sim)
    collaborative_recommendations = get_collaborative_recommendations(movies,  df_ratings, user_id, collaborative_n)

    # Find common movies in both sets of recommendations
    common_movies = set(content_recommendations) & set(collaborative_recommendations)

    # Create a list of ranked recommendations
    ranked_recommendations = list(common_movies) + list(set(content_recommendations) - common_movies) + list(set(collaborative_recommendations) - common_movies)

    # Return the top content_n + collaborative_n recommendations
    print('Hybrid recommendations obtained...')
    return ranked_recommendations[:content_n + collaborative_n]

def get_recommendations(user_id, title):
    user_favorite_movie_category = determine_category(title, df0, df1, df2)

    movies = None
    cosine_sim = None
    df_ratings = None

    # Based on the category, use the corresponding cosine similarity matrix and weights
    if user_favorite_movie_category == 'df0':
        movies = df0
        cosine_sim = df0_cosine_sim
        df_ratings = df0_movie_ratings
        content_based_weight = content_based_weight_0
        collaborative_based_weight = collaborative_based_weight_0
        hybrid_model_weight = hybrid_model_weight_0
    elif user_favorite_movie_category == 'df1':
        movies = df1
        cosine_sim = df1_cosine_sim
        df_ratings = df1_movie_ratings
        content_based_weight = content_based_weight_1
        collaborative_based_weight = collaborative_based_weight_1
        hybrid_model_weight = hybrid_model_weight_1
    elif user_favorite_movie_category == 'df2':
        movies = df2
        cosine_sim = df2_cosine_sim
        df_ratings = df2_movie_ratings
        content_based_weight = content_based_weight_2
        collaborative_based_weight = collaborative_based_weight_2
        hybrid_model_weight = hybrid_model_weight_2

    content_based_recommendations = get_content_based_recommendations(movies, title, cosine_sim,content_n=1)
    collaborative_based_recommendations = get_collaborative_recommendations(movies, ratings, user_id, n=1)
    hybrid_model_recommendations = get_hybrid_recommendations(title, user_id, content_n=10, collaborative_n=1)

    # Merge recommendation lists with df_ratings to get the corresponding ratings
    content_based_ratings = df_ratings[df_ratings['Title'].isin(content_based_recommendations)]
    collaborative_based_ratings = df_ratings[df_ratings['Title'].isin(collaborative_based_recommendations)]
    hybrid_model_ratings = df_ratings[df_ratings['Title'].isin(hybrid_model_recommendations)]

    # Apply weights to the ratings using .loc to avoid the SettingWithCopyWarning
    content_based_ratings.loc[:, 'Rating'] *= content_based_weight/5
    collaborative_based_ratings.loc[:, 'Rating'] *= collaborative_based_weight/5
    hybrid_model_ratings.loc[:, 'Rating'] *= hybrid_model_weight/5

    # Create dataframes for each recommendation method
    content_based_df = content_based_ratings[['Title', 'Rating']]
    collaborative_based_df = collaborative_based_ratings[['Title', 'Rating']]
    hybrid_model_df = hybrid_model_ratings[['Title', 'Rating']]

    # Concatenate all three dataframes into a single dataframe
    all_recommendations_df = pd.concat([content_based_df, collaborative_based_df, hybrid_model_df])
    all_recommendations_df = all_recommendations_df.groupby('Title', as_index=False)['Rating'].max()
    all_recommendations_df = all_recommendations_df.sort_values(by='Rating', ascending=False)
    print('Final recommendations obtained...')
    return all_recommendations_df

def recommend(user_id, movie):
    return get_recommendations(user_id, movie)

movie_list = movies

selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)
entered_user = st.text_input('Please Enter User_ID (1-6000): ')

if st.button('Show Recommendation'):
    user_id = int(entered_user)
    recommended_movie_names = recommend(user_id, selected_movie)
    recommended_movie_names
