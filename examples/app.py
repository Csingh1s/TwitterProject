# -*- coding: utf-8 -*-
import requests
import json
import urllib

from datetime import datetime

from flask import Flask, render_template, request
from flask import session

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length

from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import *
#import sqlalchemy
import tweepy
import os

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:admin@localhost/tweeter'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:admin@/tweeter?unix_socket=/cloudsql/tweeter-247304:us-central1:mysql'

app.secret_key = 'dev'

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)

consumerKey = "7FNmg12xwTmCeFIdbapPKh5ea"
consumerSecret = "fyP8qzUgZEyhG9rjII1AWecuC6KUG8OgEFoLDTOpaOIgj8Zymg"
accessToken = "1151510140362854403-BttX7aXPLQQxbRl2UcSFRcLDpVj1lK"
accessTokenKey = "3VtIebPaaQEWsXNl4NdckXFQKfGnNswSxpUTunYvqkOyt"

auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenKey)
api = tweepy.API(auth)



class HelloForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 150)])
    remember = BooleanField('Remember me')
    submit = SubmitField()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/form', methods=['GET', 'POST'])
def test_form():
    form = HelloForm()
    return render_template('form.html', form=form)


@app.route('/nav', methods=['GET', 'POST'])
def test_nav():
    return render_template('nav.html')


@app.route('/pagination', methods=['GET', 'POST'])
def test_pagination():
    db.drop_all()
    db.create_all()
    for i in range(100):
        m = Message()
        db.session.add(m)
    db.session.commit()

    page = request.args.get('page', 1, type=int)
    pagination = Message.query.paginate(page, per_page=10)
    messages = pagination.items
    return render_template('pagination.html', pagination=pagination, messages=messages)


@app.route('/utils', methods=['GET', 'POST'])
def test_utils():
    return render_template('utils.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    try:
        page = request.args.get('page', 1, type=int)
        pagination = Message.query.paginate(page, per_page=50)
        messages = []

        if "query" in request.form:
            session["query"] = request.form["query"]
            query = request.form["query"]
        elif "query" not in request.form and session.get("query") != None:
            query = session.get("query")
        else:
            return render_template('pagination.html', pagination=pagination, messages=[])

        topWords = ""

        # ================== get tweets ================= #
        if session.get(str(page)) == None and page == 1:
            maxId = 99999999999999999999
        elif session.get(str(page)) == None and page != 1:
            maxId = session.get(str(page - 1))["sinceId"] - 1
        else:
            maxId = session.get(str(page))["maxId"]

        tweets = []
        flag = False
        while (1):
            tweets_original = api.search(q=query, count=100, max_id=maxId, lang="en")
            if len(tweets_original) == 0:
                break
            for tweet in tweets_original:
                tweets.append(
                    {
                        "id" : tweet.id,
                        "created_at": str(tweet.created_at),
                        "text": tweet.text
                    }
                )
                if len(tweets) == 50:
                    flag = True
                    break
            if flag == True:
                break
            maxId = tweets_original.since_id - 1

        # ========= update session =========== #
        if len(tweets) > 0:
            session[str(page)] = {
                "maxId" : tweets[0]["id"],
                "sinceId" : tweets[len(tweets)-1]["id"],
            }
        # ================== count every word in every tweet ================= #
        for tweet in tweets:
            stweet = tweet["text"].split()
            tweet_words = {}
            top_words = []

            for word in stweet:
                if word not in tweet_words:
                    tweet_words[word] = 1
                    if len(top_words) < 10: top_words.append(word)
                    continue
                tweet_words[word] += 1

            # ================== get top 10 words ================= #
            if len(top_words) > 10:
                for word, cnt in tweet_words.items():
                    if word in tweet_words: continue
                    last_word = top_words[0]
                    last_idx = 0
                    i = 0
                    # ============ get word of max_words which has minimal count ========= #
                    for mword in top_words:
                        if tweet_words[last_word] > tweet_words[mword]:
                            last_word = mword
                            last_idx = i
                        i += 1
                    # ============ update max_words with new word ======================== #
                    if tweet_words[word] > tweet_words[last_word]:
                        top_words[last_idx] = word

            # ========== sort max_words ============ #
            i = 0
            j = 0
            for i in range(0, len(top_words)):
                for j in range(i + 1, len(top_words)):
                    if tweet_words[top_words[i]] < tweet_words[top_words[j]]:
                        tmp = top_words[i]
                        top_words[i] = top_words[j]
                        top_words[j] = tmp
                    j += 1
                i += 1

            i = 0
            tweet["topWords"] = ""
            for i in range(0, len(top_words)):
                if i != len(top_words) - 1:
                    tweet["topWords"] += top_words[i] + ", "
                    continue
                tweet["topWords"] += top_words[i]

            if topWords == "": topWords = tweet["topWords"]

        for tweet in tweets:
            messages.append(tweet)

        # ------------ log query, top words of first tweet ----------- #
        q = Query()
        q.query = query
        q.topwords = topWords
        db.session.add(q)
        db.session.commit()
        return render_template('pagination.html', pagination=pagination, messages=messages)

    except Exception as e:
        return render_template('pagination.html', pagination=pagination, messages=[])
