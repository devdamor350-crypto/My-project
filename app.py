import pickle
import streamlit as st
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import requests
import random
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import base64
from datetime import datetime
import pyttsx3
import speech_recognition as sr
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


CLIENT_ID = "70a9fb89662f4dac8d07321b259eaad7"
CLIENT_SECRET = "4d6710460d764fbbb8d8753dc094d131"

# Initialize the Spotify client
client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def recommend_books():
    st.title("📚 Book Recommendation System")
    
    # Load datasets
    books_df = pd.read_csv("Books.csv", low_memory=False)
    ratings_df = pd.read_csv("Ratings.csv", low_memory=False)

    # Select relevant columns
    books_df = books_df[['ISBN', 'Book-Title', 'Book-Author', 'Year-Of-Publication', 'Publisher', 'Image-URL-L']]
    ratings_df = ratings_df[['ISBN', 'Book-Rating']]

    # Merge books and ratings
    books_with_ratings = books_df.merge(ratings_df, on="ISBN", how="left")

    # Calculate average rating and total rating count for popular books
    popular_books = books_with_ratings.groupby(["Book-Title", "Book-Author", "Year-Of-Publication", "Publisher", "Image-URL-L"]).agg({
        "Book-Rating": ["count", "mean"]
    }).reset_index()

    # Rename columns
    popular_books.columns = ["Book-Title", "Book-Author", "Year-Of-Publication", "Publisher", "Image-URL-L", "Total-Ratings", "Avg-Rating"]

    # Sort by popularity
    top_5_books = popular_books.sort_values(by=["Total-Ratings", "Avg-Rating"], ascending=[False, False]).head(5)

    # Genres for filtering
    genres = ["Romance", "Mystery", "Sci-Fi", "Fictional", "Non-Fictional", "Paranormal", "Thriller"]



    # Display Popular Books in Row-Wise Format
    st.subheader("🔥 Top 5 Popular Books")
    for _, row in top_5_books.iterrows():
        col1, col2 = st.columns([1, 3])  # Image (1) | Details (3)
        with col1:
            st.image(row["Image-URL-L"], width=120)
        with col2:
            st.write(f"### {row['Book-Title']}")
            st.write(f"👨‍💼 **Author:** {row['Book-Author']}")
            st.write(f"📅 **Published:** {row['Year-Of-Publication']}")
            st.write(f"🏢 **Publisher:** {row['Publisher']}")
            st.write(f"⭐ **Rating:** {round(row['Avg-Rating'], 2)} ({row['Total-Ratings']} reviews)")
        st.markdown("---")  # Separator

    # Genre Selection
    st.subheader("🎭 Choose a Genre for Recommendations")
    selected_genre = st.selectbox("Select Genre", genres)

    if st.button("Show Genre-Based Recommendations"):
        recommended_genre_books = popular_books.sample(5)

        st.subheader(f"📖 Recommended Books in {selected_genre}")
        for _, row in recommended_genre_books.iterrows():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(row["Image-URL-L"], width=120)
            with col2:
                st.write(f"### {row['Book-Title']}")
                st.write(f"👨‍💼 **Author:** {row['Book-Author']}")
                st.write(f"📅 **Published:** {row['Year-Of-Publication']}")
                st.write(f"🏢 **Publisher:** {row['Publisher']}")
                st.write(f"⭐ **Rating:** {round(row['Avg-Rating'], 2)} ({row['Total-Ratings']} reviews)")
            st.markdown("---")

    # Book Selection for Recommendation
    st.subheader("🔍 Select a Book for Similar Recommendations")
    selected_book = st.selectbox("Select a Book", books_df["Book-Title"].unique())

    if st.button("Show Book Recommendations"):
        recommended_books = popular_books.sample(5)

        st.subheader(f"📌 Books Similar to {selected_book}")
        for _, row in recommended_books.iterrows():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(row["Image-URL-L"], width=120)
            with col2:
                st.write(f"### {row['Book-Title']}")
                st.write(f"👨‍💼 **Author:** {row['Book-Author']}")
                st.write(f"📅 **Published:** {row['Year-Of-Publication']}")
                st.write(f"🏢 **Publisher:** {row['Publisher']}")
                st.write(f"⭐ **Rating:** {round(row['Avg-Rating'], 2)} ({row['Total-Ratings']} reviews)")
            st.markdown("---")  # Separator

    st.write("📌 **Select a genre & book to get recommendations!** 🎉")

\
    


def recommend_movies():
    st.title("🎬Movie Recommender System")
    

    # Load the new dataset
    file_path = 'imdb_top_1000.csv'
    movies = pd.read_csv(file_path)

    # Prepare movie tags for similarity calculation
    movies['tags'] = movies['Genre'] + ' ' + movies['Overview'] + ' ' + movies['Director'] + ' ' + movies['Star1'] + ' ' + movies['Star2'] + ' ' + movies['Star3'] + ' ' + movies['Star4']

    cv = CountVectorizer(stop_words='english')
    tag_matrix = cv.fit_transform(movies['tags'])
    similarity = cosine_similarity(tag_matrix)

    # Movie Recommendation Function
    def recommend(movie):
        movie = movie.lower()
        index = movies[movies['Series_Title'].str.lower() == movie].index

        if index.empty:
            return []

        index = index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

        recommended_movies = []
        for i in distances[1:11]:  # Top 10 recommendations
            row = movies.iloc[i[0]]
            cast = f"{row['Star1']}, {row['Star2']}, {row['Star3']}, {row['Star4']}"
            recommended_movies.append((row['Series_Title'], row['IMDB_Rating'], row['Poster_Link'].replace("_SX300", "_SX700"), row['Overview'], row['Gross'], row['Runtime'], cast))

        return recommended_movies

    # Genre-based Recommendation Function
    def recommend_by_genre(genre):
        genre = genre.lower()
        genre_matches = movies[movies['Genre'].str.contains(genre, case=False, na=False)]

        recommended_movies = []
        for _, row in genre_matches.head(10).iterrows():
            cast = f"{row['Star1']}, {row['Star2']}, {row['Star3']}, {row['Star4']}"
            recommended_movies.append((row['Series_Title'], row['IMDB_Rating'], row['Poster_Link'].replace("_SX300", "_SX700"), row['Overview'], row['Gross'], row['Runtime'], cast))

        return recommended_movies

    # Get Top 5 Most Viewed Movies
    def get_top_5_movies():
        top_movies = movies.sort_values(by='No_of_Votes', ascending=False).head(5)

        top_5_movies = []
        for _, row in top_movies.iterrows():
            cast = f"{row['Star1']}, {row['Star2']}, {row['Star3']}, {row['Star4']}"
            top_5_movies.append((row['Series_Title'], row['IMDB_Rating'], row['Poster_Link'].replace("_SX300", "_SX700"), row['Overview'], row['Gross'], row['Runtime'], cast))

        return top_5_movies

    # Get Random Movies
    def get_random_movies():
        random_movies = movies.sample(5)

        random_movie_list = []
        for _, row in random_movies.iterrows():
            cast = f"{row['Star1']}, {row['Star2']}, {row['Star3']}, {row['Star4']}"
            random_movie_list.append((row['Series_Title'], row['IMDB_Rating'], row['Poster_Link'].replace("_SX300", "_SX700"), row['Overview'], row['Gross'], row['Runtime'], cast))

        return random_movie_list


    # Display Top 5 Most Viewed Movies
    top_5_movies = get_top_5_movies()
    if top_5_movies:
        st.markdown("<h2 style='color: #FFD700;'>🔥 Top 5 Most Viewed Movies:</h2>", unsafe_allow_html=True)

        cols = st.columns(5)

        for idx, (movie, rating, poster, overview, gross, runtime, cast) in enumerate(top_5_movies):
            with cols[idx]:
                st.image(poster, use_container_width=True)
                st.markdown(f"**{movie}**")
                st.markdown(f"⭐ **Rating:** {rating}")

    # Display Random Movies
    random_movies = get_random_movies()
    if random_movies:
        st.markdown("<h2 style='color: #00FFFF;'>🎲 Popular Movies:</h2>", unsafe_allow_html=True)

        cols = st.columns(5)

        for idx, (movie, rating, poster, overview, gross, runtime, cast) in enumerate(random_movies):
            with cols[idx]:
                st.image(poster, use_container_width=True)
                st.markdown(f"**{movie}**")

    # Choose recommendation method
    option = st.selectbox("🔍 How would you like to find movies?", ("By Movie Name", "By Genre"))

    if option == "By Movie Name":
        title_list = movies['Series_Title'].values
        selected_movie = st.selectbox("🎥 Type or select a movie from the dropdown:", title_list)

        if st.button('🚀 Show Recommendations'):
            recommended_movies = recommend(selected_movie)

            st.markdown("<h2 style='color: #4CAF50;'>✨ Recommended Movies:</h2>", unsafe_allow_html=True)

            for movie, rating, poster, overview, gross, runtime, cast in recommended_movies:
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.image(poster, use_container_width=True)

                with col2:
                    st.markdown(f"**{movie}**")
                    st.markdown(f"⭐ **Rating:** {rating}")
                    st.markdown(f"_Summary:_ {overview}")
                    st.markdown(f"💰 **Revenue:** ${gross}")
                    st.markdown(f"⏳ **Duration:** {runtime}")
                    st.markdown(f"🎭 **Cast:** {cast}")

                st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

    elif option == "By Genre":
        genre_input = st.text_input("🎭 Enter a genre (e.g., Action, Comedy, Drama):")

        if genre_input:
            recommended_movies = recommend_by_genre(genre_input)

            st.markdown("<h2 style='color: #2196F3;'>🔎 Movies in Genre:</h2>", unsafe_allow_html=True)

            for movie, rating, poster, overview, gross, runtime, cast in recommended_movies:
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.image(poster, use_container_width=True)

                with col2:
                    st.markdown(f"**{movie}**")
                    st.markdown(f"⭐ **Rating:** {rating}")
                    st.markdown(f"_Summary:_ {overview}")
                    st.markdown(f"💰 **Revenue:** ${gross}")
                    st.markdown(f"⏳ **Duration:** {runtime}")
                    st.markdown(f"🎭 **Cast:** {cast}")

                st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)








def recommend_songs():
    st.title("🎵 Music Recommendation")
    
# Load dataset
    df = pd.read_csv("dataset.csv")

    # Filter only English songs
    df = df[df["track_name"].str.contains(r'^[A-Za-z0-9\s.,!?"\']+$', na=False, regex=True)]

    # Spotify API Credentials
    CLIENT_ID = "3c340935882e4eb186f1326de0b2fa00"
    CLIENT_SECRET = "6f7d1549bd9d42298d063968ad183bf8"

    # Get Spotify Access Token
    def get_spotify_token():
        auth_url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        }
        data = {"grant_type": "client_credentials"}
        response = requests.post(auth_url, headers=headers, data=data)
        return response.json().get("access_token")

    access_token = get_spotify_token()

    # Fetch album cover from Spotify
    def get_album_cover(track_name, artist):
        search_url = "https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"q": f"track:{track_name} artist:{artist}", "type": "track", "limit": 1}

        response = requests.get(search_url, headers=headers, params=params)
        if response.status_code == 200:
            items = response.json().get("tracks", {}).get("items", [])
            if items:
                return items[0]["album"]["images"][0]["url"]
        return None



    # Time-based mapping
    time_mapping = {
        "Morning": ["dance", "pop", "workout"],
        "Afternoon": ["pop", "hip-hop", "indie"],
        "Evening": ["r&b", "acoustic", "chill"],
        "Night": ["jazz", "classical", "lo-fi"]
    }

    # Get current hour
    current_hour = datetime.now().hour
    if 5 <= current_hour < 11:
        time_of_day = "Morning"
    elif 11 <= current_hour < 17:
        time_of_day = "Afternoon"
    elif 17 <= current_hour < 21:
        time_of_day = "Evening"
    else:
        time_of_day = "Night"

    st.subheader(f"🎶 {time_of_day} Vibes")

    # Filter dataset based on genre
    selected_genres = time_mapping[time_of_day]
    df_filtered = df[df["track_genre"].str.contains('|'.join(selected_genres), case=False, na=False)]
    time_songs = df_filtered.sample(n=min(5, len(df_filtered)))

    # Display song cards
    def display_song(row):
        cover_url = get_album_cover(row['track_name'], row['artists'])
        col1, col2 = st.columns([2, 2])
        if cover_url:
            col1.image(cover_url, width=200)
        with col2:
            st.write(f"**{row['track_name']}** - {row['artists']}")
            st.write(f"⭐ Popularity: {row['popularity']}")
            st.write(f"⏱ Duration: {row['duration_ms'] // 60000}:{(row['duration_ms'] // 1000) % 60:02d}")
            st.write("---")

    for _, row in time_songs.iterrows():
        display_song(row)

    # # User-selected genre-based recommendation
    # st.subheader("🎵 Explore by Genre")
    # selected_genre = st.selectbox("Pick a Genre", df["track_genre"].unique())
    # genre_songs = df[df["track_genre"] == selected_genre].sample(n=min(5, len(df[df["track_genre"] == selected_genre])))

    # for _, row in genre_songs.iterrows():
    #     display_song(row)

    # # User-selected song-based recommendations
    # st.subheader("🔍 Discover Similar Songs")
    # selected_song = st.selectbox("Pick a Song", df["track_name"].unique())
    # similar_songs = df[df["track_name"] != selected_song].sample(n=min(5, len(df[df["track_name"] != selected_song])))

    # for _, row in similar_songs.iterrows():
    #     display_song(row)

    # Additional Explore Options
    st.subheader("🔎 Explore More")
    explore_choice = st.radio("Select an Option", ["Explore by Genre", "Discover Similar Songs"])

    if explore_choice == "Explore by Genre":
        selected_genre = st.selectbox("Pick a Genre", df["track_genre"].unique(), key="explore_genre")
        explore_songs = df[df["track_genre"] == selected_genre].sample(n=min(5, len(df[df["track_genre"] == selected_genre])))
        for _, row in explore_songs.iterrows():
            display_song(row)

    elif explore_choice == "Discover Similar Songs":
        selected_song = st.selectbox("Pick a Song", df["track_name"].unique(), key="explore_song")
        explore_songs = df[df["track_name"] != selected_song].sample(n=min(5, len(df[df["track_name"] != selected_song])))
        for _, row in explore_songs.iterrows():
            display_song(row)



        
            
        
            
            
        
def recommend_diseases():
    st.markdown("<h1 style='text-align: center; color: #ffffff;'>💊 Health Care Recommendation System 🩺</h1>", unsafe_allow_html=True)
    st.write("Select the symptoms and get your predicted disease with relevant precautions and recommendations.")

# Load datasets
    description = pd.read_csv("description.csv")
    precautions = pd.read_csv("precautions_df.csv")
    medications = pd.read_csv("medications.csv")
    diets = pd.read_csv("diets.csv")
    workout = pd.read_csv("workout_df.csv")
    doctors = pd.read_csv("doctors.csv")
    symptoms_df = pd.read_csv("symtoms_df.csv")
    tips = pd.read_csv("health_tips.csv")

    # Load ML Model
    svc_model = pickle.load(open("svc.pkl", "rb"))
    dataset = pd.read_csv("Training.csv")
    all_symptoms = dataset.columns[:-1].tolist()

    # Label datasets
    le = LabelEncoder()
    le.fit(dataset['prognosis'])


    # ---------------- BMI / Health Score Checker ------------------
    st.subheader("📏 BMI & Health Score Checker")
    height = st.number_input("Enter your height (in cm):", min_value=50.0, max_value=250.0, step=0.5)
    weight = st.number_input("Enter your weight (in kg):", min_value=10.0, max_value=200.0, step=0.5)

    if height > 0 and weight > 0:
        bmi = weight / ((height / 100) ** 2)
        st.markdown(f"**BMI: {bmi:.2f}**")
        if bmi < 18.5:
            st.warning("Underweight")
        elif 18.5 <= bmi < 25:
            st.success("Normal weight")
        elif 25 <= bmi < 30:
            st.info("Overweight")
        else:
            st.error("Obese")

    # ---------------- Daily Tip ------------------
    st.subheader("💡 Daily Health Tip")
    tip = random.choice(tips['Tip'].tolist())
    st.info(tip)

    # ---------------- Voice Input ------------------
    st.subheader("🎙 Voice Input (Optional)")
    selected_symptoms = []

    if st.button("🎤 Speak your symptoms"):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Listening... Speak your symptoms (e.g., headache, cough)")
            try:
                audio = r.listen(source, timeout=5)
                voice_text = r.recognize_google(audio)
                voice_text_cleaned = voice_text.lower().replace(" ", "_")
                detected_symptoms = [symptom for symptom in all_symptoms if symptom.replace("_", "") in voice_text_cleaned.replace("_", "")]
                if detected_symptoms:
                    st.success(f"Detected symptoms: {', '.join(sym.replace('_', ' ') for sym in detected_symptoms)}")
                    selected_symptoms = detected_symptoms

                    # Auto Predict after voice input
                    st.subheader("🔍 Auto-Prediction Result")
                    input_vector = [1 if symptom in selected_symptoms else 0 for symptom in all_symptoms]
                    input_df = pd.DataFrame([input_vector], columns=all_symptoms)
                    prediction_encoded = svc_model.predict(input_df)[0]
                    predicted_disease = le.inverse_transform([prediction_encoded])[0]
                    st.success(f"🩺 Predicted Disease: **{predicted_disease.replace('_', ' ')}**")

                    # Description
                    desc = description[description['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]['Description']
                    if not desc.empty:
                        st.subheader("📃 Disease Description")
                        st.write(desc.values[0])

                    # Precautions
                    pre = precautions[precautions['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
                    if not pre.empty:
                        st.subheader("🛡 Precautions")
                        for val in pre.iloc[0][1:]:
                            st.write(f"- {val}")

                    # Medications
                    med = medications[medications['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
                    if not med.empty:
                        st.subheader("💊 Medications")
                        for val in med['Medication']:
                            st.write(f"- {val}")

                    # Workout
                    wo = workout[workout['disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
                    if not wo.empty:
                        st.subheader("🏃 Workouts")
                        for val in wo['workout']:
                            st.write(f"- {val}")

                    # Diet
                    diet = diets[diets['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
                    if not diet.empty:
                        st.subheader("🥗 Diet Suggestions")
                        for val in diet['Diet']:
                            st.write(f"- {val}")

                    # Doctors
                    doc = doctors[doctors['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
                    if not doc.empty:
                        st.subheader("👨‍⚕️ Doctor Suggestions")
                        for i in range(len(doc)):
                            st.markdown(f"- **{doc.iloc[i]['Doctor_Name']}**, *{doc.iloc[i]['Specialization']}* ({doc.iloc[i]['Location']})")

                    # Risk Meter
                    st.subheader("📊 Disease Risk Level Meter")
                    risk_level = random.choice(['Low', 'Moderate', 'High'])
                    color_map = {"Low": "green", "Moderate": "orange", "High": "red"}
                    fig, ax = plt.subplots(figsize=(5, 0.5))
                    ax.barh(["Risk Level"], [1], color=color_map[risk_level])
                    ax.set_xlim(0, 1)
                    ax.set_title(f"Risk: {risk_level}", fontsize=14)
                    ax.axis("off")
                    st.pyplot(fig)

                    # PDF Download using BytesIO
                    buffer = BytesIO()
                    c = canvas.Canvas(buffer)
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(50, 800, "Health Recommendation Report")
                    c.setFont("Helvetica", 12)
                    c.drawString(50, 770, f"Disease: {predicted_disease.replace('_', ' ')}")
                    c.drawString(50, 750, f"Precautions: {', '.join(pre.iloc[0][1:].values)}")
                    c.drawString(50, 730, f"Medications: {', '.join(med['Medication'].values)}")
                    c.drawString(50, 710, f"Workout: {', '.join(wo['workout'].values)}")
                    c.drawString(50, 690, f"Diet: {', '.join(diet['Diet'].values)}")
                    c.save()
                    buffer.seek(0)
                    st.download_button(label="📥 Download Report as PDF", data=buffer, file_name="Health_Report.pdf", mime="application/pdf")
                else:
                    st.warning("No symptoms detected.")
            except Exception as e:
                st.error(f"Could not recognize. Error: {e}")

    # ---------------- Manual Selection ------------------
    if not selected_symptoms:
        selected_symptoms = st.multiselect("Select Symptoms", [s.replace("_", " ") for s in all_symptoms])

    # ---------------- Manual Prediction ------------------
    # ---------------- Manual Prediction ------------------
    if st.button("🔍 Predict Disease (Manual)"):
        selected_symptoms = [s.replace(" ", "_") for s in selected_symptoms]
        if not selected_symptoms:
            st.warning("Please select symptoms")
        else:
            input_vector = [1 if symptom in selected_symptoms else 0 for symptom in all_symptoms]
            input_df = pd.DataFrame([input_vector], columns=all_symptoms)
            prediction_encoded = svc_model.predict(input_df)[0]
            predicted_disease = le.inverse_transform([prediction_encoded])[0]
            st.success(f"🩺 Predicted Disease: **{predicted_disease.replace('_', ' ')}**")

            # Description
            desc = description[description['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]['Description']
            if not desc.empty:
                st.subheader("📃 Disease Description")
                st.write(desc.values[0])

            # Precautions
            pre = precautions[precautions['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
            if not pre.empty:
                st.subheader("🛡 Precautions")
                for val in pre.iloc[0][1:]:
                    st.write(f"- {val}")

            # Medications
            med = medications[medications['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
            if not med.empty:
                st.subheader("💊 Medications")
                for val in med['Medication']:
                    st.write(f"- {val}")

            # Workout
            wo = workout[workout['disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
            if not wo.empty:
                st.subheader("🏃 Workouts")
                for val in wo['workout']:
                    st.write(f"- {val}")

            # Diet
            diet = diets[diets['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
            if not diet.empty:
                st.subheader("🥗 Diet Suggestions")
                for val in diet['Diet']:
                    st.write(f"- {val}")

            # Doctors
            doc = doctors[doctors['Disease'].str.lower().str.replace("_", "") == predicted_disease.lower().replace("_", "")]
            if not doc.empty:
                st.subheader("👨‍⚕️ Doctor Suggestions")
                for i in range(len(doc)):
                    st.markdown(f"- **{doc.iloc[i]['Doctor_Name']}**, *{doc.iloc[i]['Specialization']}* ({doc.iloc[i]['Location']})")

            # Risk Meter
            st.subheader("📊 Disease Risk Level Meter")
            risk_level = random.choice(['Low', 'Moderate', 'High'])
            color_map = {"Low": "green", "Moderate": "orange", "High": "red"}
            fig, ax = plt.subplots(figsize=(5, 0.5))
            ax.barh(["Risk Level"], [1], color=color_map[risk_level])
            ax.set_xlim(0, 1)
            ax.set_title(f"Risk: {risk_level}", fontsize=14)
            ax.axis("off")
            st.pyplot(fig)

            # PDF Download using BytesIO
            buffer = BytesIO()
            c = canvas.Canvas(buffer)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, 800, "Health Recommendation Report")
            c.setFont("Helvetica", 12)
            c.drawString(50, 770, f"Disease: {predicted_disease.replace('_', ' ')}")
            c.drawString(50, 750, f"Precautions: {', '.join(pre.iloc[0][1:].values)}")
            c.drawString(50, 730, f"Medications: {', '.join(med['Medication'].values)}")
            c.drawString(50, 710, f"Workout: {', '.join(wo['workout'].values)}")
            c.drawString(50, 690, f"Diet: {', '.join(diet['Diet'].values)}")
            c.save()
            buffer.seek(0)
            st.download_button(label="📥 Download Report as PDF", data=buffer, file_name="Health_Report.pdf", mime="application/pdf")


            # [Add same blocks again as above if needed]

    # Footer
    st.markdown("---")
    st.markdown("💙 Developed with care - Stay Healthy!")


# Main App
st.markdown("""
    <h1 style='
        color: #FF0000;
        font-size: 48px;
        text-align: center;
        font-weight: bold;
        text-shadow: 0 0 10px #e7feff, 0 0 20px #e7feff;
    '>
        🤖 Recommendation Prediction System
    </h1>
""", unsafe_allow_html=True)



# Styling
st.markdown("""
    <style>
        .title-text {
            text-align: center;
            font-size: 40px;
            color: #ffffff;
            padding: 20px;
            background: linear-gradient(to right, #ff6e7f, #bfe9ff);
            border-radius: 15px;
            margin-bottom: 30px;
        }
        .nav-box {
            color: #000000;
            text-align: center;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 15px;
            background-color: #f4f4f4;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
        }
        .nav-box:hover {
            background-color: #000000;
            color: #ffffff;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    /* Change sidebar heading */
    [data-testid="stSidebar"] h2 {
        color: #B59410 !important;
    }

    /* Change sidebar radio label text */
    [data-testid="stSidebar"] .css-1v3fvcr {
        color: #B59410 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown("## 📂 Navigation Panel")
app_mode = st.sidebar.radio(
    "Choose a module:",
    ["🏠 Home", "🎬 Movie Recommendation", "🎵 Music Recommendation", "📚 Book Recommendation", "💊 Healthcare Recommendation"]
)

# Use your local image
import streamlit as st
import base64

# Function to convert image to base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
        return encoded
    except FileNotFoundError:
        st.error(f"Image file not found: {image_path}")
        return ""

# Provide the image path (make sure img22.jpg is in the same folder as this script)
image_path = "img42.png"
img_base64 = get_base64_image(image_path)

# Set background image only if the image was loaded successfully
if img_base64:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{img_base64}");
            background-size: 100% 100%;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- Sidebar Logo Image ---
import base64

def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_base64 = get_img_as_base64("ing45.jpg")

st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{
        background-image: url("data:image/jpg;base64,{img_base64}");
        background-size: 100% 100%;
        background-repeat: no-repeat;
        background-position: center;
    }}
    </style>
""", unsafe_allow_html=True)


# App Logic
if app_mode == "🏠 Home":
    st.markdown("### 👋 Welcome to the Personalized Recommendation System")
    st.markdown("This platform offers personalized suggestions based on your preferences in **Movies**, **Music**, **Books**, and **Healthcare**.")
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="nav-box">🎬 Movie Recommendation</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="nav-box">🎵 Music Recommendation</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="nav-box">📚 Book Recommendation</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="nav-box">💊 Healthcare Prediction</div>', unsafe_allow_html=True)

    

elif app_mode == "🎬 Movie Recommendation":
    recommend_movies()

elif app_mode == "🎵 Music Recommendation":
    recommend_songs()

elif app_mode == "📚 Book Recommendation":
    recommend_books()

elif app_mode == "💊 Healthcare Recommendation":
    recommend_diseases()

# Footer
st.markdown("---")
st.markdown("<center>Made with ❤️ by SKY.M | Powered by Machine Learning</center>", unsafe_allow_html=True)
