# Movie recommender system

## Overview

The purpose of this project is to build a Flask web application of a movie recommendation system in addition to apply sentiment analysis on each movie reviews with Python. 
It can be split into two main tasks:

Building a recommendation engine that suggest movies based on how a movie is similar to other movies (Content-based Filtering) and how a user is similar to other users (Collaborative Filtering).

Building a sentiment analysis model to predict the sentiment (positive or negative) of movie reviews.

## Project System Design
 ![image](https://user-images.githubusercontent.com/80493805/177148885-29eb0619-9e5e-4c9e-a8eb-e2df065a950f.png)

As mentioned in the above image, in this project we aim to build a web application using Flask framework in python. 
The idea beginning the project goes as follow:
After inserting the movie title by the user, the recommendation system will suggest the best recommendation.
Using TMDB API we receive/gather the information about the movie that the user is looking for and all other suggested movies.
Scrapp the best reviews from IMDB website.
Predict each review if it is a positive or a negative one using the sentiment analysis model.
