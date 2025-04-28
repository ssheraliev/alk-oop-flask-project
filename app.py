from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, get_flashed_messages
import sqlite3
import os
import json
from datetime import datetime
import uuid
import traceback
import bcrypt

DATABASE_PATH = 'db/mystical_tale.db'

# Database connection function
def get_db_connection():
    """establishes connection to DB"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row # access columns by name
    return conn

# Database initialization function
def init_db():
    """init db tables & populate story content"""
    try:
        print("Initializing database...")
        db_dir = os.path.dirname(DATABASE_PATH)
        os.makedirs(db_dir, exist_ok=True)

        conn = get_db_connection()
        c = conn.cursor()
        print("DB connection established")

        # users creation table
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("'users' table creation executed")

        # characters creation table
        c.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL, -- Foreign key linking to the users table
            name TEXT NOT NULL,
            race TEXT NOT NULL,
            archetype TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        print("'characters' table creation executed")
        
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
        print("'save_games' table creation executed")

        # story_nodes table
        c.execute('''
        CREATE TABLE IF NOT EXISTS story_nodes (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("'story_nodes' table creation executed")

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
        
        # initial story nodes population (if not done already)
        c.execute("SELECT COUNT(*) FROM story_nodes")
        if c.fetchone()[0] == 0:
            print("Populating initial story nodes...")
            populate_story_nodes(c)
        else:
            print("Story nodes already populated")

        conn.commit()
        print("Database connection committed")
        conn.close()
        print("DB init finished successfully")
    except sqlite3.Error as e:
        print(f"DB init error: {e}")
        print(traceback.format_exc())
        if conn:
            conn.rollback()
            conn.close()
        print("DB init failed due to SQLite error")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during database initialization: {e}")
        print(traceback.format_exc())
        if conn:
            conn.rollback()
            conn.close()
        print("DB init failed due to unexpected error")
        raise
        
# Story content initialization
def populate_story_nodes(cursor):
    """Populate story_nodes and choices table"""
    try:
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('start', 'You awaken in a clearing bathed in moonlight, your mind hazy with forgotten memories. The last thing you recall is following a strange light deep into the Whispering Woods.\n\nAll around you, ancient trees loom like silent guardians, their branches swaying gently as if communicating in a language long forgotten by mortal kind.\n\nA soft, melodic voice calls to you from the shadows: "Awakened one, you have crossed the threshold between worlds. The veil is thin tonight, and your destiny awaits."')
        )

        # adding choices -> start node
        choices = [
            ('c1', 'start', 'Call out to the mysterious voice', 'voice_response'),
            ('c2', 'start', 'Examine your surroundings more carefully', 'examine_clearing'),
            ('c3', 'start', 'Try to remember how you got here', 'remember_path')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )

        # response node
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('voice_response', '"Who\'s there?" you call into the darkness, your voice echoing strangely among the trees.\n\nA figure emerges from the shadows—a woman with skin like polished alabaster and eyes that shift colors like opals in the moonlight. Her hair floats around her as if suspended in water, and her flowing garments seem woven from starlight itself.\n\n"I am Elysia, Guardian of the Threshold," she says, her voice resonating in your mind rather than your ears. "Few mortals find their way here, and fewer still are chosen by the Whispering Woods."')
        )

        # choices for response node
        choices = [
            ('c4', 'voice_response', '"Chosen? What do you mean I was chosen?"', 'chosen_explanation'),
            ('c5', 'voice_response', '"Where exactly am I? What is this place?"', 'place_explanation'),
            ('c6', 'voice_response', '"I need to return home immediately."', 'return_home')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )

        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('examine_clearing', 'You take a moment to study your surroundings more carefully. The clearing is perfectly circular, as if carved with purpose rather than formed by nature. Small luminescent mushrooms form a ring around its edge, pulsing with a gentle blue light.\n\nAt the center, where you awoke, the grass forms an intricate spiral pattern that seems to glow faintly under the moonlight. You notice strange symbols etched into the surrounding trees—ancient runes that seem to shimmer when you focus directly on them.\n\nA small stone altar stands at the far edge of the clearing, covered in moss and bearing a small silver bowl filled with clear liquid that reflects the stars above with impossible clarity.')
        )

        # adding choices for clearing node
        choices = [
            ('c7', 'examine_clearing', 'Approach the stone altar', 'approach_altar'),
            ('c8', 'examine_clearing', 'Examine the glowing mushroom ring', 'examine_mushrooms'),
            ('c9', 'examine_clearing', 'Study the strange runes on the trees', 'study_runes')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )

        # path node for the record
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('remember_path', 'You close your eyes, focusing on the fragments of memory that drift through your mind like autumn leaves on a stream.\n\nYou recall walking home along your usual path when a strange light—like a lantern but with a flame of shifting colors—appeared among the trees. Something about it called to you, compelling you to follow as it danced just beyond your reach.\n\nDeeper and deeper it led you into the woods, until the path disappeared and the trees grew ancient and strange. The air became thick with the scent of moss and night-blooming flowers, and faint music seemed to play from nowhere and everywhere.\n\nThen came a threshold—a sensation of passing through a veil of cool mist—and then... darkness, until you awoke here in this clearing.')
        )

        # choices for path node
        choices = [
            ('c10', 'remember_path', 'Try to find the path you came from', 'find_path'),
            ('c11', 'remember_path', 'Call out for help', 'call_help'),
            ('c12', 'remember_path', 'Look for the colored light you followed', 'seek_light')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )

        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('chosen_explanation', 'Elysia\'s smile is both warm and mysterious. "The Woods have a consciousness all their own—ancient and inscrutable. They do not call to mortals without purpose."\n\nShe gestures to the trees around you, which seem to lean in slightly as if listening.\n\n"There is an imbalance growing between your world and ours. The boundaries weaken, and creatures that should remain in shadow have begun to cross. The Woods sensed something in you—a potential, a key perhaps—that might help restore what has been broken."\n\nShe extends her hand, a small pendant dangling from her fingers. It appears to be a silver leaf veined with luminescent blue.\n\n"This imbalance threatens both our realms. Will you help us discover what causes it and set things right?"')
        )

        # choices for chosen_explanation node
        choices = [
            ('c13', 'chosen_explanation', 'Accept the pendant and offer your help', 'accept_quest'),
            ('c14', 'chosen_explanation', 'Ask for more information before deciding', 'more_information'),
            ('c15', 'chosen_explanation', 'Refuse and insist on returning home', 'refuse_quest')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )

        # placeholder nodes for remaining paths
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
            ('more_information', 'You ask Elysia for more information before deciding.'),
            ('refuse_quest', 'You refuse the pendant and insist on finding your way home as soon as possible.')
        ]

        for node_id, text in placeholder_nodes:
            cursor.execute("INSERT INTO story_nodes (id, text) VALUES (?, ?)", (node_id, text))
            # placeholder choice for each node that leads back to start
            cursor.execute(
                "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), node_id, 'Continue your journey', 'start')
            )
    except sqlite3.Error as e:
        print(f"Error populating story nodes: {e}")
        raise


# Database helper functions
def get_character(character_id):
    """fetching a character by their ID"""
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
        print(f"Database error in get_character: {e}")
        print(traceback.format_exc())
        return None
    finally:
        if conn:
            conn.close()

def get_story_node(node_id):
    """fetching story node and associated choices by node ID"""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # getting node text
        c.execute("SELECT * FROM story_nodes WHERE id = ?", (node_id,))
        node = c.fetchone()

        if not node:
            return None

        # getting choices for the node
        c.execute("SELECT * FROM choices WHERE node_id = ?", (node_id,))
        choices = c.fetchall()

        result = dict(node)
        result['choices'] = [dict(choice) for choice in choices]

        return result
    except sqlite3.Error as e:
        print(f"Database error in get_story_node: {e}")
        print(traceback.format_exc())
        return None
    finally:
        if conn:
            conn.close()

def get_save_games_for_character(character_id):
    """fetching save games for a specific character"""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM save_games WHERE character_id = ? ORDER BY timestamp DESC", (character_id,))
        save_games = [dict(row) for row in c.fetchall()]
        return save_games
    except sqlite3.Error as e:
        print(f"Database error in get_save_games_for_character: {e}")
        print(traceback.format_exc())
        return []
    finally:
        if conn:
            conn.close()

def get_all_save_games_for_user(user_id):
    """fetching all save games for a specific user, including story snippet"""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # query modification to join with characters and story_nodes
        c.execute("""
            SELECT sg.*, c.name AS character_name, c.race, c.archetype, sn.text AS story_text_snippet
            FROM save_games sg
            JOIN characters c ON sg.character_id = c.id
            JOIN story_nodes sn ON sg.current_node_id = sn.id -- Join with story_nodes
            WHERE c.user_id = ? -- Filter by the logged-in user's ID
            ORDER BY sg.timestamp DESC
        """, (user_id,))
        save_games = [dict(row) for row in c.fetchall()]
        return save_games
    except sqlite3.Error as e:
        print(f"Database error in get_all_save_games_for_user: {e}")
        print(traceback.format_exc())
        return []
    finally:
        if conn:
            conn.close()

# Main application factory function
def create_app():
    """function to create and configure the Flask"""
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

    # DB init when the app context is ready
    with app.app_context():
        init_db()

    # --- defining each route ---

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/game')
    def game():
        try:
            messages = get_flashed_messages()
            print(f"Debug: Messages retrieved in /game route: {messages}")

            user_id = session.get('user_id')
            if not user_id:
                flash('Please log in to play the game.')
                return redirect(url_for('login'))

            character_id = session.get('character_id')

            # checking if a character is selected for the logged-in user **
            if not character_id:
                 # If logged in but there is no character, redirects to character creation
                 flash('Please select or create a character to play.')
                 return redirect(url_for('character_creation'))


            # proceed to get game data
            character = get_character(character_id)
            current_node_id = session.get('current_node_id', 'start')
            current_node = get_story_node(current_node_id)
            save_games = get_save_games_for_character(character_id)

            if not character or not current_node:
                flash('Error loading character or story data. Please try again.')
                # session character info clearance if data is invalid
                session.pop('character_id', None)
                session.pop('current_node_id', None)
                return redirect(url_for('index'))

                
    try:
        character_id = session.get('character_id')
        current_node_id = session.get('current_node_id')
        
        if not character_id or not current_node_id:
            flash('Cannot save game: no active character or game state')
            return redirect(url_for('index'))
        
        # Get character info for the save name
        character = get_character(character_id)
        if not character:
            flash('Error retrieving character information')
            return redirect(url_for('game'))
            
        save_name = f"{character['name']}'s Journey - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO save_games (id, character_id, current_node_id, save_name) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), character_id, current_node_id, save_name)
        )
        conn.commit()
        conn.close()
        
        flash('Your journey has been preserved in the mystical archives')
        return redirect(url_for('game'))
    except Exception as e:
        app.logger.error(f"Error in save_game: {e}")
        app.logger.error(traceback.format_exc())
        flash('An error occurred while saving your game. Please try again.')
        return redirect(url_for('game'))

@app.route('/load-game/<save_id>')
def load_game(save_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM save_games WHERE id = ?", (save_id,))
        save_game = c.fetchone()
        conn.close()
        
        if save_game:
            # Setting character and node in session
            session['character_id'] = save_game['character_id']
            session['current_node_id'] = save_game['current_node_id']
            flash('Your journey continues from where you left off')
        else:
            flash('Could not load the saved game')
        
        return redirect(url_for('game'))
    except Exception as e:
        app.logger.error(f"Error in load_game: {e}")
        app.logger.error(traceback.format_exc())
        flash('An error occurred while loading your game. Please try again.')
        return redirect(url_for('load_saves'))

@app.route('/load-saves')
def load_saves():
    try:
        save_games = get_all_save_games()
        return render_template('load_game.html', save_games=save_games)
    except Exception as e:
        app.logger.error(f"Error in load_saves: {e}")
        app.logger.error(traceback.format_exc())
        flash('An error occurred while retrieving saved games. Please try again.')
        return redirect(url_for('index'))

@app.route('/clear-session')
def clear_session():
    session.clear()
    return redirect(url_for('index'))

# Adding error handler for 500 error messages
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500 error: {error}")
    app.logger.error(traceback.format_exc())
    return render_template('error.html', error="A mystical disturbance has occurred. The arcane energies require rebalancing."), 500

# Adding error handler for 404 error message
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="The path you seek does not exist in this realm."), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)