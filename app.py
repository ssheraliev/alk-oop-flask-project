from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, get_flashed_messages
import sqlite3
import os
import json
from datetime import datetime
import uuid
import traceback
import bcrypt
import requests

# DB directory and path
DATABASE_PATH = 'db/mystical_tale.db'

# Database connection function
def get_db_connection():
    """connection to the SQLite database"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Database initialization
def init_db():
    """init database tables and populate initial story"""
    try:
        print("Initializing database...")
        db_dir = os.path.dirname(DATABASE_PATH)
        os.makedirs(db_dir, exist_ok=True)
        print(f"Database directory {db_dir} ensured.")

        conn = get_db_connection()
        c = conn.cursor()
        print("Database connection established.")

        # Users table creation
        print("Attempting to create 'users' table...")
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("'users' table creation statement executed.")

        # Characters table creation
        print("Attempting to create 'characters' table...")
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
        print("'characters' table creation statement executed.")

        # save_games table creation
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
        print("'save_games' table creation statement executed.")

        # story_nodes table creation
        c.execute('''
        CREATE TABLE IF NOT EXISTS story_nodes (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("'story_nodes' table creation statement executed.")

        # Choices table linked to story nodes
        c.execute('''
        CREATE TABLE IF NOT EXISTS choices (
            id TEXT PRIMARY KEY,
            node_id TEXT NOT NULL,
            text TEXT NOT NULL,
            next_node_id TEXT NOT NULL,
            FOREIGN KEY (node_id) REFERENCES story_nodes(id)
        )
        ''')
        print("'choices' table creation statement executed.")

        # initial story nodes population - if not done already
        c.execute("SELECT COUNT(*) FROM story_nodes")
        if c.fetchone()[0] == 0:
            print("Populating initial story nodes...")
            populate_story_nodes(c)
            print("Story nodes population finished.")
        else:
            print("Story nodes already populated.")

        conn.commit()
        print("Database connection committed.")
        conn.close()
        print("Database connection closed.")
        print("Database initialization finished successfully.")
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        print(traceback.format_exc())
        if conn:
            conn.rollback()
            conn.close()
        print("Database initialization failed due to SQLite error.")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during database initialization: {e}")
        print(traceback.format_exc())
        if conn:
            conn.rollback()
            conn.close()
        print("Database initialization failed due to unexpected error.")
        raise


# Story content initialization
def populate_story_nodes(cursor):
    """populating the story_nodes and choices tables with initial content"""
    try:
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

        # clearing node
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

        # the path node for the record
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('remember_path', 'You close your eyes, focusing on the fragments of memory that drift through your mind like autumn leaves on a stream.\n\nYou recall walking home along your usual path when a strange light—like a lantern but with a flame of shifting colors—appeared among the trees. Something about it called to you, compelling you to follow as it danced just beyond your reach.\n\nDeeper and deeper it led you into the woods, until the path disappeared and the trees grew ancient and strange.The air became thick with the scent of moss and night-blooming flowers, and faint music seemed to play from nowhere and everywhere.\n\nThen came a threshold—a sensation of passing through a veil of cool mist—and then... darkness, until you awoke here in this clearing.')
        )

        # adding choices for path node
        choices = [
            ('c10', 'remember_path', 'Try to find the path you came from', 'find_path'),
            ('c11', 'remember_path', 'Call out for help', 'call_help'),
            # choice leads to 'seek_light'
            ('c12', 'remember_path', 'Look for the colored light you followed', 'seek_light')
        ]
        cursor.executemany(
            "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
            choices
        )

        # chosen explanation node
        cursor.execute(
            "INSERT INTO story_nodes (id, text) VALUES (?, ?)",
            ('chosen_explanation', 'Elysia\'s smile is both warm and mysterious. "The Woods have a consciousness all their own—ancient and inscrutable. They do not call to mortals without purpose."\n\nShe gestures to the trees around you, which seem to lean in slightly as if listening.\n\n"There is an imbalance growing between your world and ours. The boundaries weaken, and creatures that should remain in shadow have begun to cross. The Woods sensed something in you—a potential, a key perhaps—that might help restore what has been broken."\n\nShe extends her hand, a small pendant dangling from her fingers. It appears to be a silver leaf veined with luminescent blue.\n\n"This imbalance threatens both our realms. Will you help us discover what causes it and set things right?"')
        )

        # adding choices for chosen_explanation node
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
            ('accept_quest', 'You accept the pendant from Elysia and promise to help restore balance between the realms.'),
            ('more_information', 'You ask Elysia for more information before deciding.'),
            ('refuse_quest', 'You refuse the pendant and insist on finding your way home as soon as possible.')
        ]

        for node_id, text in placeholder_nodes:
            if node_id != 'seek_light':
                 cursor.execute("INSERT INTO story_nodes (id, text) VALUES (?, ?)", (node_id, text))
                 cursor.execute(
                     "INSERT INTO choices (id, node_id, text, next_node_id) VALUES (?, ?, ?, ?)",
                     (str(uuid.uuid4()), node_id, 'Continue your journey', 'start')
                 )

        # checking if 'seek_light' node exists
        cursor.execute(
            "INSERT OR IGNORE INTO story_nodes (id, text) VALUES (?, ?)",
            ('seek_light', 'You look around for any sign of the colored light that led you here. The clearing is still bathed in moonlight, but the strange light is nowhere to be seen. The path you followed seems to have vanished, leaving you truly lost in the Whispering Woods.')
        )
        # we offer players 'Roll the dice!'

    except sqlite3.Error as e:
        print(f"Error populating story nodes: {e}")
        raise


# Database helper functions
def get_character(character_id):
    """character fetching by their ID"""
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
    """story node and its associated choices fetching by node ID"""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # getting the node text
        c.execute("SELECT * FROM story_nodes WHERE id = ?", (node_id,))
        node = c.fetchone()

        if not node:
            return None

        # getting the choices for the node
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
    """save games fetching for a specific character"""
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
    """save games fetching for a specific user, including story snippet"""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # query to join with characters & story_nodes
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

# LLM API configuration
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
OLLAMA_MODEL_NAME = os.environ.get('OLLAMA_MODEL_NAME', 'gemma3')

def generate_story_content(prompt_text):
    """API call to generate dynamic journey story content"""
    try:
        payload = {
            "model": OLLAMA_MODEL_NAME,
            "prompt": prompt_text,
            "stream": False # full response
        }
        headers = {
            "Content-Type": "application/json"
        }

        print(f"Calling Ollama API at: {OLLAMA_API_URL}")
        print(f"Prompt: {prompt_text[:200]}...") # 200 chars (head) of prompt

        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers)
        response.raise_for_status() # exception - bad status codes (4xx or 5xx)

        result = response.json()
        generated_text = result.get('response', '').strip()

        print(f"Ollama Response (first 200 chars): {generated_text[:200]}...")

        return generated_text

    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
        print(traceback.format_exc())
        return f"Error generating content: Could not connect to Ollama or API error. Details: {e}"
    except Exception as e:
        print(f"An unexpected error occurred during Ollama call: {e}")
        print(traceback.format_exc())
        return f"Error generating content: An unexpected error occurred. Details: {e}"


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

    # defining game route early, as other routes redirect to it
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

            # checking if character is selected for the logged-in user **
            if not character_id:
                 # if logged in but there is no character, redirect to character creation
                 flash('Please select or create a character to play.')
                 return redirect(url_for('character_creation'))

            character = get_character(character_id)
            if not character:
                flash('Error loading character data. Please try again.')
                session.pop('character_id', None)
                session.pop('current_node_id', None)
                return redirect(url_for('index'))

            current_node_id = session.get('current_node_id', 'start')

            # --- LLM generated or Pre - Defined content ---
            if current_node_id == 'dynamic':
                # LLM content retrieval directly from the session
                story_text_to_display = session.get('dynamic_story_text', 'Error loading dynamic story.')
                choices_to_display = session.get('dynamic_choices', [])
                current_node_info = None # No pre-defined node object when LLM generated

                # for the next LLM call to have context, managing state in /roll-the-dice.

            else:
                # fetching pre - defined content from the database
                current_node_info = get_story_node(current_node_id)
                if not current_node_info:
                    flash('Error loading static story data. Please try again.')
                    # clearing session if pre-defined node data is invalid
                    session.pop('current_node_id', None)
                    return redirect(url_for('game'))

                story_text_to_display = current_node_info['text']
                choices_to_display = current_node_info['choices']
                session.pop('dynamic_story_text', None)
                session.pop('dynamic_choices', None)


            # checking if there is a content to display
            if not story_text_to_display:
                 flash('Story content is missing. Please try again.')
                 # attempt to reset to start or index if story content is missing
                 session.pop('current_node_id', None)
                 session.pop('dynamic_story_text', None)
                 session.pop('dynamic_choices', None)
                 return redirect(url_for('game'))

            # fetching save games for the character
            save_games = get_save_games_for_character(character_id)

            return render_template(
                'game.html',
                character=character,
                current_node=current_node_info, # should be None if LLM generated
                story_text_to_display=story_text_to_display, # text to display
                choices_to_display=choices_to_display, # list of choices
                save_games=save_games,
                flashed_messages=messages,
                current_node_id=current_node_id
            )

        except Exception as e:
            print(f"Error in game route: {e}")
            print(traceback.format_exc())
            flash('An unexpected error occurred. Please try again.')
            return redirect(url_for('index'))

    # roll_the_dice route, where game.html calls url_for('roll_the_dice')
    @app.route('/roll-the-dice', methods=['POST'])
    def roll_the_dice():
        try:
            user_id = session.get('user_id')
            character_id = session.get('character_id')
            current_node_id = session.get('current_node_id')

            if not user_id or not character_id or not current_node_id:
                flash('Cannot roll the dice: game state is not valid.')
                return redirect(url_for('index'))

            # retrieving current story text to provide context to the LLM
            if current_node_id == 'dynamic':
                 current_story_text = session.get('dynamic_story_text', '')
                 # getting chosen LLM choice text if passed from the choice form
                 chosen_dynamic_choice = request.form.get('chosen_dynamic_choice')
                 if chosen_dynamic_choice:
                      # appending chosen choice to the context for the next API call
                      current_story_text += f"\nPlayer chose: {chosen_dynamic_choice}"
                      print(f"Debug: Player chose dynamic choice: {chosen_dynamic_choice}")

            else:
                current_node = get_story_node(current_node_id)
                if not current_node:
                     flash('Error getting current story context.')
                     # redirecting back if current node not found
                     return redirect(url_for('game'))
                current_story_text = current_node['text']
                # if player rolls the dice from pre-defined game, clearing previous LLM provided content
                session.pop('dynamic_story_text', None)
                session.pop('dynamic_choices', None)


            # getting character information for context
            character = get_character(character_id)
            character_info = f"Character: {character['name']}, {character['race']} {character['archetype']}" if character else "Your character"


            # --- Game prompt for the LLM ---
            prompt_text = f"""
            The player's character is a {character_info}.
            They are currently at this point in the story:
            "{current_story_text}"

            Generate the next part of the story (around 100-200 words) and then provide exactly three distinct choices for the player to make.
            Format your response clearly with the story text first, followed by the choices.
            Use the following format for choices:
            Choice 1: [Text of the first choice]
            Choice 2: [Text of the second choice]
            Choice 3: [Text of the third choice]

            Ensure the choices are logical continuations of the story and offer different paths. The story should continue directly from the current situation.
            """

            # Ollama API call to generate content
            generated_content = generate_story_content(prompt_text)

            # --- parsing generated content ---
            story_text = ""
            choices = []
            choice_lines = []
            in_choices_section = False

            lines = generated_content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # parsing as if "Choice X:" format
                if line.startswith("Choice 1:"):
                    in_choices_section = True
                    choice_lines.append(line[len("Choice 1:"):].strip())
                elif line.startswith("Choice 2:"):
                    in_choices_section = True
                    choice_lines.append(line[len("Choice 2:"):].strip())
                elif line.startswith("Choice 3:"):
                    in_choices_section = True
                    choice_lines.append(line[len("Choice 3:"):].strip())
                elif in_choices_section:
                     if choice_lines:
                          choice_lines[-1] += (" " + line).strip()
                else:
                    # accumulating story text before the choices section
                    story_text += line + "\n"

            # cleaning up story text (which removes trailing newlines)
            story_text = story_text.strip()

            # converting parsed choice into the template format
            dynamic_choices = []
            for i, choice_text in enumerate(choice_lines):
                 # generating a unique ID for each dynamic choice
                 choice_id = f"dynamic-{uuid.uuid4()}"
                 dynamic_choices.append({
                     'id': choice_id,
                     'node_id': 'dynamic',
                     'text': choice_text,
                     'next_node_id': 'dynamic' # choices bring player to the next LLM generated node
                 })

            # --- storing LLM generated content ---
            # story parts will not be saved to our DB
            session['dynamic_story_text'] = story_text
            session['dynamic_choices'] = dynamic_choices
            session['current_node_id'] = 'dynamic'

            flash('The dice have been rolled! Your journey takes a new turn.')
            return redirect(url_for('game'))

        except Exception as e:
            print(f"Error in roll_the_dice route: {e}")
            print(traceback.format_exc())
            flash('An error occurred while rolling the dice. Please try again.')
            return redirect(url_for('game'))

    # --- route to return to the pre-defined game ---
    @app.route('/return-to-static')
    def return_to_static():
        try:
            user_id = session.get('user_id')
            if not user_id:
                flash('Please log in to return to the static path.')
                return redirect(url_for('login'))

            # resetting the current node ID to the starting node
            session['current_node_id'] = 'start'
            # LLM generated content deletion
            session.pop('dynamic_story_text', None)
            session.pop('dynamic_choices', None)

            flash('You have returned to the beginning of the static path.')
            return redirect(url_for('game'))

        except Exception as e:
            print(f"Error in return_to_static route: {e}")
            print(traceback.format_exc())
            flash('An error occurred while returning to the static path. Please try again.')
            return redirect(url_for('game'))


    @app.route('/character-creation', methods=['GET', 'POST'])
    def character_creation():
        # ** checking if a user is logged in for both GET and POST **
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to create a character.')
            return redirect(url_for('login'))

        if request.method == 'POST':
            try:
                name = request.form.get('name')
                race = request.form.get('race')
                archetype = request.form.get('archetype')

                if not name or not race or not archetype:
                    flash('All fields are required')
                    return redirect(url_for('character_creation'))

                character_id = str(uuid.uuid4())

                conn = get_db_connection()
                c = conn.cursor()
                try:
                    # user_id in the INSERT
                    c.execute(
                        "INSERT INTO characters (id, user_id, name, race, archetype) VALUES (?, ?, ?, ?, ?)",
                        (character_id, user_id, name, race, archetype)
                    )
                    conn.commit()
                    session['character_id'] = character_id
                    session['current_node_id'] = 'start'

                    flash(f'Welcome, {name}! Your mystical adventure awaits!')
                    return redirect(url_for('game'))
                except sqlite3.Error as e:
                    conn.rollback()
                    print(f"SQLite error in character creation: {e}")
                    print(traceback.format_exc())
                    flash('Database error occurred during character creation. Please try again.')
                    return redirect(url_for('character_creation'))
                finally:
                    conn.close()
            except Exception as e:
                print(f"Unexpected error during character creation: {e}")
                print(traceback.format_exc())
                flash('An unexpected error occurred during character creation. Please try again.')
                return redirect(url_for('character_creation'))

        return render_template('character_creation.html')

    @app.route('/make-choice', methods=['POST'])
    def make_choice():
        try:
            if not session.get('character_id'):
                return redirect(url_for('character_creation'))

            choice_id = request.form.get('choice_id')

            if not choice_id:
                flash('Invalid choice')
                return redirect(url_for('game'))

            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT next_node_id FROM choices WHERE id = ?", (choice_id,))
            choice = c.fetchone()
            conn.close()

            if choice:
                session['current_node_id'] = choice['next_node_id']
                # ** flashing a new message to indicate choice was made **
                flash('Your choice has been made.')
                # LLM content deletion from session to move to pre-defined game
                session.pop('dynamic_story_text', None)
                session.pop('dynamic_choices', None)


            return redirect(url_for('game'))
        except Exception as e:
            print(f"Error in make_choice: {e}")
            print(traceback.format_exc())
            flash('An error occurred while processing your choice. Please try again.')
            return redirect(url_for('game'))

    @app.route('/save-game', methods=['POST'])
    def save_game():
        try:
            character_id = session.get('character_id')
            current_node_id = session.get('current_node_id')
            save_name = request.form.get('save_name')

            if not save_name:
                 flash('Please provide a name for your save.')
                 return redirect(url_for('game'))

            # preventing saving LLM generated game state directly
            if current_node_id == 'dynamic':
                 flash('Cannot save game during a dynamic story segment.')
                 return redirect(url_for('game'))


            if not character_id or not current_node_id:
                flash('Cannot save game: no active character or game state')
                return redirect(url_for('index'))

            character = get_character(character_id)
            if not character:
                flash('Error retrieving character information')
                return redirect(url_for('game'))

            conn = get_db_connection()
            c = conn.cursor()
            try:
                # ** save_name in the INSERT **
                c.execute(
                    "INSERT INTO save_games (id, character_id, current_node_id, save_name) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), character_id, current_node_id, save_name)
                )
                conn.commit()
                flash(f'Your journey has been preserved as "{save_name}" in the mystical archives')
                return redirect(url_for('game'))
            except sqlite3.Error as e:
                conn.rollback()
                print(f"SQLite error in save_game: {e}")
                print(traceback.format_exc())
                flash('Database error occurred while saving your game. Please try again.')
                return redirect(url_for('game'))
            finally:
                conn.close()
        except Exception as e:
            print(f"Error in save_game: {e}")
            print(traceback.format_exc())
            flash('An unexpected error occurred while saving your game. Please try again.')
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
                session['character_id'] = save_game['character_id']
                session['current_node_id'] = save_game['current_node_id']
                # deleting LLM generated content from session
                session.pop('dynamic_story_text', None)
                session.pop('dynamic_choices', None)
                flash('Your journey continues from where you left off')
            else:
                flash('Could not load the saved game')

            return redirect(url_for('game'))
        except Exception as e:
            print(f"Error in load_game: {e}")
            print(traceback.format_exc())
            flash('An error occurred while loading your game. Please try again.')
            return redirect(url_for('load_saves'))

    @app.route('/load-saves')
    def load_saves():
        try:
            # checking if a user is logged in
            user_id = session.get('user_id')
            if not user_id:
                flash('Please log in to view your saved games.')
                return redirect(url_for('login'))

            # ** getting games for the logged-in user **
            save_games = get_all_save_games_for_user(user_id)

            return render_template('load_game.html', save_games=save_games)

        except Exception as e:
            print(f"Error in load_saves: {e}")
            print(traceback.format_exc())
            flash('An error occurred while retrieving saved games. Please try again.')
            return redirect(url_for('index'))

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            try:
                username = request.form.get('username')
                password = request.form.get('password')

                if not username or not password:
                    flash('Please provide both username and password.')
                    return redirect(url_for('signup'))

                conn = get_db_connection()
                c = conn.cursor()

                # checking if username already exists
                c.execute("SELECT id FROM users WHERE username = ?", (username,))
                existing_user = c.fetchone()

                if existing_user:
                    flash('Username already exists. Please pick a different name.')
                    conn.close()
                    return redirect(url_for('signup'))

                # hashing password for user
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                # inserting new user into DB
                c.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed_password)
                )
                conn.commit()
                conn.close()

                flash('Account created successfully! Please log in.')
                 # redirecting to login once signup is complete
                return redirect(url_for('login'))

            except sqlite3.Error as e:
                if conn:
                    conn.rollback()
                    conn.close()
                print(f"SQLite error during signup: {e}")
                print(traceback.format_exc())
                flash('Database error occurred during signup. Please try again.')
                return redirect(url_for('signup'))
            except Exception as e:
                print(f"Unexpected error during signup: {e}")
                print(traceback.format_exc())
                flash('An unexpected error occurred during signup. Please try again.')
                return redirect(url_for('signup'))

        return render_template('signup.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Please provide both username and password.')
                return redirect(url_for('login'))

            conn = get_db_connection()
            c = conn.cursor()

            # request to get user from the database
            c.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            conn.close()

            if user:
                # password verification
                if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                    # if password is correct, letting user in
                    session['user_id'] = user['id']
                    flash(f'Welcome back, {user["username"]}!')
                    # redirecting to game page
                    return redirect(url_for('game'))
                else:
                    # if password is incorrect
                    flash('Invalid username or password.')
                    return redirect(url_for('login'))
            else:
                # if user is not found
                flash('Invalid username or password.')
                return redirect(url_for('login'))

        return render_template('login.html')


    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('You have been logged out.')
        return redirect(url_for('index'))

    @app.route('/delete-save/<save_id>', methods=['POST'])
    def delete_save(save_id):
        try:
            user_id = session.get('user_id')
            if not user_id:
                flash('Please log in to delete saved games.')
                return redirect(url_for('login'))

            conn = get_db_connection()
            c = conn.cursor()

            # if saved game belongs to logged-in user
            c.execute("""
                SELECT sg.id
                FROM save_games sg
                JOIN characters c ON sg.character_id = c.id
                WHERE sg.id = ? AND c.user_id = ?
            """, (save_id, user_id))
            save_to_delete = c.fetchone()

            if save_to_delete:
                # in case, saved game exists and belongs to the user, letting to delete it
                c.execute("DELETE FROM save_games WHERE id = ?", (save_id,))
                conn.commit()
                flash('Saved game deleted successfully.')
            else:
                # in case of saved game doesn't exist or doesn't belong to the user
                flash('Could not delete the specified saved game.')

            conn.close()

            return redirect(url_for('load_saves'))
        except Exception as e:
            print(f"Error in delete_save route: {e}")
            print(traceback.format_exc())
            flash('An error occurred while deleting the saved game. Please try again.')
            return redirect(url_for('load_saves'))


    @app.route('/clear-session')
    def clear_session():
        session.clear()
        return redirect(url_for('index'))

    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        print(f"500 error: {error}")
        print(traceback.format_exc())
        return render_template('error.html', error="A mystical disturbance has occurred. The arcane energies require rebalancing."), 500

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error="The path you seek does not exist in this realm."), 404

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)