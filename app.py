from flask import Flask, render_template
import os
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# App Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():

@app.route('/character_creation')
def character_creation():

@app.route('/make-choice')
def make_choice():

@app.route('/save-game')
def save_game():

@app.route('/load_game/<save_id>')
def load_game(save_id):

@app.route('/load_saves')
def load_saves():

@app.route('/clear_session')
def clear_session():                     
