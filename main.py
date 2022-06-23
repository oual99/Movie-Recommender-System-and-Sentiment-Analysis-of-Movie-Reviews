<<<<<<< HEAD
import numpy as np
import pandas as pd
import bs4 as bs
from flask import Flask, render_template, request
from sklearn.feature_extraction.text import CountVectorizer
from urllib.request import urlopen
import json
import nltk
import re
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import pickle
# nltk.download('stopwords')
# nltk.download('wordnet')

app = Flask(__name__)
data_movie = pd.read_csv("data_movies_final.csv")


################################# collaborative part ############################
with open('collaborative\decomposed_matrix.npy', 'rb') as f:
    decomposed_matrix = np.load(f)
f = open("collaborative\list_movie_id_collaborative.pkl", 'rb')
movie_id = pickle.load(f)
f.close()

correlation_matrix = np.corrcoef(decomposed_matrix)


def get_recommend_collabotive(id):
    movie_index = movie_id.index(id)
    correlation_movie = correlation_matrix[movie_index]
    list_movies = pd.DataFrame(correlation_movie)
    temp = list_movies.sort_values(by=[0], ascending=False).index[0:20]
    buts = []
    for i in temp:
        movie = movie_id[i]
        but = data_movie[data_movie["id"] == movie]
        if(movie != id):
            buts.append([movie, but["title"].values[0],
                        but["score"].values[0]])
    temp = pd.DataFrame(buts).sort_values(by=[2], ascending=False)[0:12]
    return temp[0]


################################# sentiment analysis part ########################
# Defining stop_words and lemmatizer
stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()
loaded_SVM = pickle.load(open('sentimentAnalysis\SVM_model', 'rb'))
count_vect = pickle.load(open('sentimentAnalysis\count_vect', 'rb'))
# Defining clean_text function


def clean_text(text):
    text = re.sub(r'[^A-Za-z0-9]+', ' ', text)
    text = text.lower()
    text = [lemmatizer.lemmatize(token) for token in text.split(" ")]
    text = [lemmatizer.lemmatize(token, "v") for token in text]
    text = [word for word in text if not word in stop_words]
    text = " ".join(text)
    return text


################################## contenantBased part ##########################
f = open('contentBased\cosin_sim_final.pkl', 'rb')
cosin_sim_final = pickle.load(f)
f.close()
f = open('contentBased\indx.pkl', 'rb')
indx = pickle.load(f)
f.close()
# Construct a reverse map of indices and movie titles
indices = pd.Series(data_movie.index, index=data_movie['id'])


def get_recommend_contenantBased(id):
 # Get the index of the movie that matches the title
    idx = indices[id]
  # Get the pairwsie similarity scores of all movies with that movie
    sim_scores = []
    for i, sim in enumerate(cosin_sim_final[idx]):
        sim_scores.append([indx[i], sim])

    # Sort the movies based on the similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the scores of the 10 most similar movies
    sim_scores = sim_scores[0:50]

    # Get the movie indices
    movie_indices = [i[0] for i in sim_scores]

    rank_data = data_movie[['id', 'score']].iloc[movie_indices].sort_values(
        'score', ascending=False)

    if id in rank_data.values:
        rank_data = rank_data.drop([rank_data[rank_data['id'] == id].index[0]])

    rank_data = rank_data[0:12]
    # Return the top 15 most similar movies
    return rank_data['id']

################################ popular ####################################


def popular_movie():
    temp = data_movie[["id", "score"]].sort_values(
        by=["score"], ascending=False)
    return temp["id"]




@app.route("/")
@app.route("/home", methods=["GET", "POST"])
def home():
    return render_template('home.html', home=1)


@app.route("/list_movies", methods=["GET", "POST"])
def list_movies():
    movie_name = request.form["movie_name"]
    reslt = {}
    ########################################## search for movie ######################################
    url = "https://api.themoviedb.org/3/search/movie?api_key=08e7c1d222c497dbff1a47ee16c5ea0c&language=en-US&query=" + \
        str(movie_name)
    url = url.replace("\n", " ").encode('ascii', 'ignore').decode('ascii')
    a = url.replace(" ", "%20").encode('ascii', 'ignore').decode('ascii')
    response = urlopen(a)
    data_json = json.loads(response.read())

    for i in data_json['results']:
        if(str(i['poster_path']) != "None"):
            try:
                reslt[i['id']] = {
                    'link': "https://image.tmdb.org/t/p/original"+str(i['poster_path']),
                    'title': i['title'],
                    'date': str(i['release_date']),
                    "vote_average": str(i["vote_average"]),
                    "vote_count": str(i["vote_count"])
                }
            except:
                pass

    return render_template('home.html', detail=None, list_movie=reslt, home=0)


def sentence(data):
    j = 0
    temp = ""
    for i in data:
        temp += j*" , "+i["name"]
        j += 1
        if(j > 1):
            j = 1
    return temp


@app.route("/movie", methods=["GET", "POST"])
def movie():

    button = request.form["button"]

    ######################################## movie detail################################
    url = "https://api.themoviedb.org/3/movie/" + \
        str(button)+"?api_key=08e7c1d222c497dbff1a47ee16c5ea0c"

    response = urlopen(url)
    data_json = json.loads(response.read())
    imdb_id = data_json["imdb_id"]
    detail = {
        'link': "https://image.tmdb.org/t/p/original"+str(data_json['poster_path']),
        "release date": str(data_json["release_date"]),
        "title": data_json["title"],
        "vote average": str(data_json["vote_average"]),
        "vote count": str(data_json["vote_count"]),
        "runtime": str(data_json["runtime"])
    }

    detail["spoken languages"] = sentence(data_json["spoken_languages"])
    detail["genre"] = sentence(data_json["genres"])
    detail['production companies'] = sentence(
        data_json["production_companies"])
    detail["production countries"] = sentence(
        data_json["production_countries"])

    detail["overview"] = str(data_json["overview"])
    ########################################## director and casts ##################################
    url = "https://api.themoviedb.org/3/movie/" + \
        str(button)+"/credits?api_key=08e7c1d222c497dbff1a47ee16c5ea0c&language=en-US"
    response = urlopen(url)
    data_json = json.loads(response.read())
    casts = []
    for i, j in enumerate(data_json['cast']):
        if(j["profile_path"] != None):
            casts.append({
                'cast_name': j['name'],
                'profile_path': "https://image.tmdb.org/t/p/original"+j["profile_path"]
            })

        if(i > 4):
            break
    temp = []
    for j in data_json['crew']:
        if j["job"] == "Director":
            temp.append(j)
    detail["Director"] = sentence(temp)
    detail["casts"] = casts
    ########################################## get recommend collaborative ########################
    try:
        movies_recommended = get_recommend_collabotive(str(button))
    
        movies = []
        for i in movies_recommended:
            url = "https://api.themoviedb.org/3/movie/" + \
                str(i)+"?api_key=08e7c1d222c497dbff1a47ee16c5ea0c"
            response = urlopen(url)
            data_json = json.loads(response.read())
            movie = {
                'id': i,
                'link': "https://image.tmdb.org/t/p/original"+str(data_json['poster_path']),
                "title": data_json["title"]
            }
            movies.append(movie)
        detail["collaborative_recommender"] = movies
    except:
        movies_recommended = popular_movie()
        movies = []
        for j, i in enumerate(movies_recommended):
            url = "https://api.themoviedb.org/3/movie/" + \
                str(i)+"?api_key=08e7c1d222c497dbff1a47ee16c5ea0c"
            response = urlopen(url)
            data_json = json.loads(response.read())
            movie = {
                'id': i,
                'link': "https://image.tmdb.org/t/p/original"+str(data_json['poster_path']),
                "title": data_json["title"]
            }
            movies.append(movie)
            if(j > 10):
                break
        detail["collaborative_recommender"] = movies
    ######################################### get recommend contenant Based ######################
    try:
        movies_recommended = get_recommend_contenantBased(str(button))
       
        movies = []
        for i in movies_recommended:
            url = "https://api.themoviedb.org/3/movie/" + \
                str(i)+"?api_key=08e7c1d222c497dbff1a47ee16c5ea0c"
            response = urlopen(url)
            data_json = json.loads(response.read())
            movie = {
                'id': i,
                'link': "https://image.tmdb.org/t/p/original"+str(data_json['poster_path']),
                "title": data_json["title"]
            }
            movies.append(movie)
        detail["contenantBased_recommender"] = movies
    except:
        detail["contenantBased_recommender"] = None
    ####################################### analyse commantaire ################################
    url = urlopen(
        'https://www.imdb.com/title/{}/reviews?spoiler=hide&sort=helpfulnessScore&dir=desc'.format(imdb_id)).read()
    soup = bs.BeautifulSoup(url, 'lxml')
    soup_result = soup.find_all("div", {"class": "text show-more__control"})

    list_reviews = []
    for i, reviews in enumerate(soup_result):
        test = count_vect.transform([clean_text(reviews.text)]).toarray()
        list_reviews.append({
            'text': reviews.text,
            'predict': loaded_SVM.predict(test)
        })
        if(i > 10):
            break

    detail["reviews"] = list_reviews
    return render_template('home.html', detail=detail, list_movie={})


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
=======
from website import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> origin
