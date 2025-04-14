from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import json
from datetime import datetime
import uuid
import traceback

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Used for session management

# DB dir
os.makedirs('db', exist_ok=True)
DATABASE_PATH = 'db/mystical_tale.db'

# Database helper function
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# database init
def init_db():
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # characters table
        c.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            race TEXT NOT NULL,
            archetype TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # save_games table
        c.execute('''
        CREATE TABLE IF NOT EXISTS save_games (
            id TEXT PRIMARY KEY,
            character_id TEXT NOT NULL,
            current_node_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            save_name TEXT NOT NULL,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
        ''')
        
        # story_nodes table
        c.execute('''
        CREATE TABLE IF NOT EXISTS story_nodes (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # choices table linked to story nodes
        c.execute('''
        CREATE TABLE IF NOT EXISTS choices (
            id TEXT PRIMARY KEY,
            node_id TEXT NOT NULL,
            text TEXT NOT NULL,
            next_node_id TEXT NOT NULL,
            FOREIGN KEY (node_id) REFERENCES story_nodes(id)
        )
        ''')
        
        # initial story nodes population - if not done already
        c.execute("SELECT COUNT(*) FROM story_nodes")
        if c.fetchone()[0] == 0:
            populate_story_nodes(c)
        
        conn.commit()
        conn.close()
        app.logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        app.logger.error(f"Database initialization error: {e}")
        app.logger.error(traceback.format_exc())
        if conn:
            conn.rollback()
            conn.close()
        raise

# story content initialization
def populate_story_nodes(cursor):
    try:
        # start node
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('start', 'You awaken in a clearing bathed in moonlight, your mind hazy with forgotten memories. The last thing you recall is following a strange light deep into the Whispering Woods.\n\nAll around you, ancient trees loom like silent guardians, their branches swaying gently as if communicating in a language long forgotten by mortal kind.\n\nA soft, melodic voice calls to you from the shadows: "Awakened one, you have crossed the threshold between worlds. The veil is thin tonight, and your destiny awaits."')
        )
        
        # adding choices for start node
        choices = [
            ('c1', 'start', 'Call out to the mysterious voice', 'voice_response'),
            ('c2', 'start', 'Examine your surroundings more carefully', 'examine_clearing'),
            ('c3', 'start', 'Try to remember how you got here', 'remember_path')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )
        
        # voice response node
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('voice_response', '"Who\'s there?" you call into the darkness, your voice echoing strangely among the trees.\n\nA figure emerges from the shadows—a woman with skin like polished alabaster and eyes that shift colors like opals in the moonlight. Her hair floats around her as if suspended in water, and her flowing garments seem woven from starlight itself.\n\n"I am Elysia, Guardian of the Threshold," she says, her voice resonating in your mind rather than your ears. "Few mortals find their way here, and fewer still are chosen by the Whispering Woods."')
        )
        
        # adding choices for voice_response node
        choices = [
            ('c4', 'voice_response', '"Chosen? What do you mean I was chosen?"', 'chosen_explanation'),
            ('c5', 'voice_response', '"Where exactly am I? What is this place?"', 'place_explanation'),
            ('c6', 'voice_response', '"I need to return home immediately."', 'return_home')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )
        
        # examining clearing node
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('examine_clearing', 'You take a moment to study your surroundings more carefully. The clearing is perfectly circular, as if carved with purpose rather than formed by nature. Small luminescent mushrooms form a ring around its edge, pulsing with a gentle blue light.\n\nAt the center, where you awoke, the grass forms an intricate spiral pattern that seems to glow faintly under the moonlight. You notice strange symbols etched into the surrounding trees—ancient runes that seem to shimmer when you focus directly on them.\n\nA small stone altar stands at the far edge of the clearing, covered in moss and bearing a small silver bowl filled with clear liquid that reflects the stars above with impossible clarity.')
        )
        
        # adding choices for examine_clearing node
        choices = [
            ('c7', 'examine_clearing', 'Approach the stone altar', 'approach_altar'),
            ('c8', 'examine_clearing', 'Examine the glowing mushroom ring', 'examine_mushrooms'),
            ('c9', 'examine_clearing', 'Study the strange runes on the trees', 'study_runes')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )
        
        # Remember path node
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('remember_path', 'You close your eyes, focusing on the fragments of memory that drift through your mind like autumn leaves on a stream.\n\nYou recall walking home along your usual path when a strange light—like a lantern but with a flame of shifting colors—appeared among the trees. Something about it called to you, compelling you to follow as it danced just beyond your reach.\n\nDeeper and deeper it led you into the woods, until the path disappeared and the trees grew ancient and strange. The air became thick with the scent of moss and night-blooming flowers, and faint music seemed to play from nowhere and everywhere.\n\nThen came a threshold—a sensation of passing through a veil of cool mist—and then... darkness, until you awoke here in this clearing.')
        )
        
        # Add choices for remember_path node
        choices = [
            ('c10', 'remember_path', 'Try to find the path you came from', 'find_path'),
            ('c11', 'remember_path', 'Call out for help', 'call_help'),
            ('c12', 'remember_path', 'Look for the colored light you followed', 'seek_light')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )
        
        # Chosen explanation node
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('chosen_explanation', 'Elysia\'s smile is both warm and mysterious. "The Woods have a consciousness all their own—ancient and inscrutable. They do not call to mortals without purpose."\n\nShe gestures to the trees around you, which seem to lean in slightly as if listening.\n\n"There is an imbalance growing between your world and ours. The boundaries weaken, and creatures that should remain in shadow have begun to cross. The Woods sensed something in you—a potential, a key perhaps—that might help restore what has been broken."\n\nShe extends her hand, a small pendant dangling from her fingers. It appears to be a silver leaf veined with luminescent blue.\n\n"This imbalance threatens both our realms. Will you help us discover what causes it and set things right?"')
        )
        
        # Add choices for chosen_explanation node
        choices = [
            ('c13', 'chosen_explanation', 'Accept the pendant and offer your help', 'accept_quest'),
            ('c14', 'chosen_explanation', 'Ask for more information before deciding', 'more_information'),
            ('c15', 'chosen_explanation', 'Refuse and insist on returning home', 'refuse_quest')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )
        
        # Add placeholder nodes for remaining paths
        placeholder_nodes = [
            ('place_explanation', 'You ask Elysia about this mysterious place, and she explains that you are in the Whispering Woods, a realm that exists between the mortal world and the fae realms.'),
            ('return_home', 'When you express your need to return home, Elysia\'s expression becomes serious. "The way back is not as simple as you might hope..."'),
            ('approach_altar', 'You approach the stone altar cautiously, drawn by the mysterious liquid in the silver bowl.'),
            ('examine_mushrooms', 'You kneel down to examine the luminescent mushrooms that form a perfect circle around the clearing.'),
            ('study_runes', 'As you approach one of the trees to study the strange runes etched into its bark, the symbols seem to shift and dance before your eyes.'),
            ('find_path', 'You search the edges of the clearing for any sign of the path you followed to get here.'),
            ('call_help', 'You call out for help, your voice echoing strangely among the ancient trees.'),
            ('seek_light', 'You look around for any sign of the colored light that led you here.'),
            ('accept_quest', 'You accept the pendant from Elysia and promise to help restore balance between the realms.'),
            ('more_information', 'You ask Elysia for more information before making your decision.'),
            ('refuse_quest', 'You refuse the pendant and insist on finding your way home as soon as possible.')
        ]
        
        for node_id, text in placeholder_nodes:
            cursor.execute("INSERT INTO story_nodes (id, text) VALUES (?, ?)", (node_id, text))
            # Add a placeholder choice for each node that leads back to start for now
            cursor.execute(
                "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), node_id, 'Continue your journey', 'start')
            )
    except sqlite3.Error as e:
        app.logger.error(f"Error populating story nodes: {e}")
        raise

def get_character(character_id):
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        character = c.fetchone()
        if character:
            return dict(character)
        return None
    except sqlite3.Error as e:
        app.logger.error(f"Database error in get_character: {e}")
        app.logger.error(traceback.format_exc())
        return None
    finally:
        if conn:
            conn.close()

def get_story_node(node_id):
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get the node text
        c.execute("SELECT * FROM story_nodes WHERE id = ?", (node_id,))
        node = c.fetchone()
        
        if not node:
            return None
        
        # Get the choices for this node
        c.execute("SELECT * FROM choices WHERE node_id = ?", (node_id,))
        choices = c.fetchall()
        
        result = dict(node)
        result['choices'] = [dict(choice) for choice in choices]
        
        return result
    except sqlite3.Error as e:
        app.logger.error(f"Database error in get_story_node: {e}")
        app.logger.error(traceback.format_exc())
        return None
    finally:
        if conn:
            conn.close()

def get_save_games_for_character(character_id):
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM save_games WHERE character_id = ? ORDER BY timestamp DESC", (character_id,))
        save_games = [dict(row) for row in c.fetchall()]
        return save_games
    except sqlite3.Error as e:
        app.logger.error(f"Database error in get_save_games_for_character: {e}")
        app.logger.error(traceback.format_exc())
        return []
    finally:
        if conn:
            conn.close()

def get_all_save_games():
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT sg.*, c.name, c.race, c.archetype 
            FROM save_games sg
            JOIN characters c ON sg.character_id = c.id
            ORDER BY sg.timestamp DESC
        """)
        save_games = [dict(row) for row in c.fetchall()]
        return save_games
    except sqlite3.Error as e:
        app.logger.error(f"Database error in get_all_save_games: {e}")
        app.logger.error(traceback.format_exc())
        return []
    finally:
        if conn:
            conn.close()

# Application routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    try:
        character_id = session.get('character_id')
        if character_id:
            # If character is in session, get their info
            character = get_character(character_id)
            current_node_id = session.get('current_node_id', 'start')
            current_node = get_story_node(current_node_id)
            save_games = get_save_games_for_character(character_id)
            
            if not character or not current_node:
                flash('Error loading character or story data. Please try again.')
                return redirect(url_for('index'))
            
            return render_template(
                'game.html',
                character=character,
                current_node=current_node,
                save_games=save_games
            )
        else:
            # If no character, redirect to character creation
            return redirect(url_for('character_creation'))
    except Exception as e:
        app.logger.error(f"Error in game route: {e}")
        app.logger.error(traceback.format_exc())
        flash('An unexpected error occurred. Please try again.')
        return redirect(url_for('index'))

@app.route('/character-creation', methods=['GET', 'POST'])
def character_creation():

@app.route('/make-choice', methods=['POST'])
def make_choice():

@app.route('/save-game', methods=['POST'])
def save_game():

@app.route('/load-game/<save_id>')
def load_game(save_id):

@app.route('/load-saves')
def load_saves():

@app.route('/clear-session')
def clear_session():           