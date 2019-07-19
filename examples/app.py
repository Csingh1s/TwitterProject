# -*- coding: utf-8 -*-
import requests
import json

from flask import Flask, render_template, request

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length

from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

import tweepy

app = Flask(__name__)
app.secret_key = 'dev'

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)

consumerKey = "7FNmg12xwTmCeFIdbapPKh5ea"
consumerSecret = "fyP8qzUgZEyhG9rjII1AWecuC6KUG8OgEFoLDTOpaOIgj8Zymg"
accessToken = "1151510140362854403-BttX7aXPLQQxbRl2UcSFRcLDpVj1lK"
accessTokenKey = "3VtIebPaaQEWsXNl4NdckXFQKfGnNswSxpUTunYvqkOyt"



class HelloForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 150)])
    remember = BooleanField('Remember me')
    submit = SubmitField()


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)


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
    #messages = [
    #    {"id" : 1},
    #]
    return render_template('pagination.html', pagination=pagination, messages=messages)


@app.route('/utils', methods=['GET', 'POST'])
def test_utils():
    return render_template('utils.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    try:
        auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
        auth.set_access_token(accessToken, accessTokenKey)
        api = tweepy.API(auth)

        # ================== get tweets ================= #
        tweets = []
        i = 0
        sinceId = 0
        query = "hello"
        tweets_original = api.search(q = query, count = 100, result_type = "recent")
        if len(tweets_original) == 0:
            return render_template('index.html')
        maxId = tweets_original[0].id

        flag = False
        while (1):
            tweets_original = api.search(q = query, count = 100, max_id = maxId)
            if len(tweets_original) == 0:
                break
            for tweet in tweets_original:
                tweets.append(
                    {
                        "created_at" : str(tweet.created_at),
                        "text" : tweet.text
                    }
                )
                if len(tweets) == 1000:
                    flag = True
                    break
            if flag == True:
                break
            maxId = tweets_original.since_id - 1

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
                    last_word=  top_words[0]
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
                for j in range(i+1, len(top_words)):
                    if tweet_words[top_words[i]] < tweet_words[top_words[j]]:
                        tmp = top_words[i]
                        top_words[i] = top_words[j]
                        top_words[j] = tmp
                    j += 1
                i += 1
            tweet["topWords"] = top_words

        # =============== log query =============== #
        query = request.form["query"]

        return render_template('index.html')

    except Exception as e:
        return render_template('index.html')
