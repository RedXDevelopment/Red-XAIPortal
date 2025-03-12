import os
import time
import webview
import json
from typing import Any, List
from threading import Thread
import firebase_admin
from firebase_admin import auth
import flask
import bcrypt
from flask_cors import CORS
from flask import Flask, send_from_directory, request, jsonify
from AutoUpdater import check_for_updates
from MiscModuleFunctions import (
    initialize_firebase,
    play_songs_indefinitely,
    verify_user,
    CheckValidation,
    register_user,
    Quick_Save,
    search_database_and_auth,
    search_database_and_auth_new,
    portal_login,
    load_json,
    save_json,
    get_value,
    set_value
)


#Improved Firebase initialization check.
firebase_initialized = initialize_firebase()

if not firebase_initialized:
    print("Fatal Error: Firebase initialization failed. Exiting.")
    exit(1) #Exit if firebase failed to initialize.

results =search_database_and_auth(email="maindirectory1998@gmail.com",Yas="Queen")
if results:
    print("Database Search Results:", results['database'])
    print("Auth Search Results:", results['auth'])
else:
    print("Failed to perform search.")
# Function to create Flask app
def create_flask_app():
    # This points to the directory where the current script is located (src folder)
    src_dir = os.path.dirname(os.path.abspath(__file__))
    # This points to the main project folder (parent directory of the src)
    project_root = os.path.dirname(src_dir)
    app = Flask(__name__, static_folder=os.path.join(project_root, 'static'), static_url_path='')
    CORS(app)  # Enable CORS
    @app.route('/')
    def index():
        json_file_path = os.path.join(project_root, 'json', 'LocalUserData.json')
        print("Attempting to load JSON from:", json_file_path)
        try:
            localdata = load_json(json_file_path)
            agreement_accepted = get_value(localdata, ['AcceptedTerms'])
            if agreement_accepted:
                return send_from_directory(os.path.join(project_root, 'html'), 'LoginRegister.html')
            else:
                return send_from_directory(os.path.join(project_root, 'html'), 'UserAgreement.html')
        except FileNotFoundError:
            print("File not found:", json_file_path)
            return "File not found error", 404
        
    @app.route('/accept-agreement', methods=['POST'])
    def accept_agreement():
        json_file_path = os.path.join(project_root, 'json', 'LocalUserData.json')
        try:
            # Load the current data
            data = load_json(json_file_path)
            # Set the agreement acceptance to True
            set_value(data, ['AcceptedTerms'], True)
            # Save the updated data
            save_json(data, json_file_path)
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            print(f"Error updating agreement status: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to update agreement status'}), 500

        
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory(os.path.join(project_root, 'css'), filename)

    @app.route('/html/<path:filename>')
    def serve_html(filename):
        return send_from_directory(os.path.join(project_root, 'html'), filename)

    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(os.path.join(project_root, 'assets'), filename)


    @app.route('/js/<path:filename>')
    def serve_js(filename):
        return send_from_directory(os.path.join(project_root, 'js'), filename)

    @app.route('/check_field', methods=['POST'])
    def check_field():
        try:
            data = request.get_json()
            field_type = data.get("field_type")
            value = data.get("value")
            is_taken = CheckValidation(field_type, value)
            return jsonify({"is_taken": is_taken})
        except Exception as e:
            print(f"Error in /check_field: {e}")
            return jsonify({"error": "Server error."}), 500

    @app.route('/login', methods=['POST'])
    def login_route():
        data = request.get_json()
        username_or_email = data.get('username')  # Retrieve username from the POST request
        password = data.get('password')  # Retrieve password from the POST request
        uid, user_info = search_database_and_auth_new(username_or_email)
        
        if user_info and bcrypt.checkpw(password.encode('utf-8'), user_info['Password'].encode('utf-8')):
            return jsonify({
                "success": True,
                "message": "Login successful",
                "username": user_info['Username'],
                "email": user_info['Email'],
                "FBToken": "some_token",
                "FBStayLoggedInToken": "some_persistent_token",
                "AcceptedTerms": True,  # Assuming you store this elsewhere or have it set
                "UserID": user_info['UID']
            })
        else:
            return jsonify({
            "success": False,
            "message": "Invalid username or password",
            "error": "Authentication failed"
        
        })
        
        print(f"Error during login: {str(e)}")
        return jsonify({"success": False, "message": "Server error", "error": str(e)}), 500

    @app.route('/register', methods=['GET'])
    def handle_register():
        try:
            data = request.get_json()
            if 'email' in data:
                print(f"Received email: {data['email']}")
            if 'password' in data:
                print(f"Received password: {data['password']}")
            if 'phone' in data:
                print(f"Received phone: {data['phone'] if data['phone'] != '' else 'blank string'}")

            return jsonify({"success": True})
        except Exception as e:
            print(f"Error in /register: {e}")
            return jsonify({"error": "Server error."}), 500

    return app

def run_flask_app():
    app = create_flask_app()
    app.run(port=5000, debug=True, use_reloader=False)

def main():
    flask_thread = Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    time.sleep(2) #Wait for Flask to start

    #Music
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    music_directory = os.path.join(project_root, 'Assets', 'audio', 'game_music')
    if os.path.exists(music_directory):
        play_songs_indefinitely(music_directory)
    else:
        print(f"Warning: Music directory not found at {music_directory}")
    
    #WebView
    webview.create_window("Login - Red-XAI Portal", "http://127.0.0.1:5000/", frameless=True, fullscreen=True)
    webview.start()

if __name__ == '__main__':
    check_for_updates()
    main()
