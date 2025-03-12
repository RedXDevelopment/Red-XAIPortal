import os
from flask import Flask, request, jsonify
import json
from typing import Any, List
import random
import pygame
import threading
import firebase_admin
from firebase_admin import credentials, firestore, auth, db
import requests

def initialize_firebase():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_path = os.path.join(base_dir, "config", "red-xai-firebase-adminsdk-fbsvc-74070c6558.json")

        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Firebase credentials file not found at {cred_path}")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://red-xai-default-rtdb.firebaseio.com/'
        })
        print("Firebase Admin initialized successfully.")
        return True
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"Error initializing Firebase Admin: {e}")
        return False

# Music functions (Make sure these are identical to your original code)
music_control = {'pause': False, 'stop': False}

def play_songs_indefinitely(directory):
    if not os.path.exists(directory):
        print(f"Error: Music directory '{directory}' not found.")
        return

    pygame.mixer.init()
    songs = [os.path.join(directory, song) for song in os.listdir(directory) if song.lower().endswith(('.mp3', '.wav'))]

    if not songs:
        print("No audio files found.")
        return

    random.shuffle(songs)

    def play_music():
        while not music_control['stop']:
            for song in songs:
                if music_control['stop']:
                    pygame.mixer.music.stop()
                    return

                pygame.mixer.music.load(song)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    if music_control['pause']:
                        pygame.mixer.music.pause()
                        while music_control['pause']:
                            pygame.time.delay(100)
                        pygame.mixer.music.unpause()
                    pygame.time.delay(100)

            random.shuffle(songs)

    music_thread = threading.Thread(target=play_music)
    music_thread.start()

    return music_thread

def pause_music():
    music_control['pause'] = True

def resume_music():
    music_control['pause'] = False
    pygame.mixer.music.unpause()

def stop_music():
    music_control['stop'] = True
    pygame.mixer.music.stop()

def verify_user():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'json', 'LocalUserData.json')
        if not os.path.exists(file_path):
            print(f"Error: LocalUserData.json not found at {file_path}")
            return None

        with open(file_path, 'r') as file:
            data = json.load(file)

        if 'FBToken' in data:
            try:
                decoded_token = auth.verify_id_token(data['FBToken'])
                return decoded_token
            except Exception as e:
                print(f"Error verifying token: {e}")
                return None
        return None
    except Exception as e:
        print(f"Error in verify_user: {e}")
        return None

def CheckValidation(field_type, value):
    try:
        db = firestore.client()
        users_ref = db.collection('users')
        query = users_ref.where(field_type, '==', value).stream()
        return any(True for _ in query)
    except Exception as e:
        print(f"Error in CheckValidation: {e}")
        return False

def register_user(user_data):
    try:
        required_fields = ['firstName', 'lastName', 'username', 'email', 'password', 'dob', 'terms']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                return {'success': False, 'error': f"Missing required field: {field}"}

        if CheckValidation('username', user_data['username']):
            return {'success': False, 'error': "Username already taken."}
        if CheckValidation('email', user_data['email']):
            return {'success': False, 'error': "Email already registered."}
        if user_data.get('phone1') and CheckValidation('phone', user_data['phone1']):
            return {'success': False, 'error': "Phone number already in use."}

        user = auth.create_user(
            email=user_data['email'],
            password=user_data['password'],
            display_name=user_data['username']
        )

        user_info = {
            'username': user_data['username'],
            'firstName': user_data['firstName'],
            'middleInitial': user_data.get('middleInitial', ''),
            'lastName': user_data['lastName'],
            'email': user_data['email'],
            'dob': user_data['dob'],
            'phone': user_data.get('phone1', ''),
            'phoneVerified': False,
            'emailVerified': False,
            'ipAddress': "0.0.0.0",
            'acceptedEULA': user_data['terms']
        }

        db.reference(f'users/{user.uid}').set(user_info)
        print(f"User {user.uid} registered successfully.")
        return {'success': True, 'message': "User registered successfully. Please verify your email."}
    except auth.AuthError as e:
        print(f"Authentication Error during registration: {e}")
        return {'success': False, 'error': f"Authentication error: {e}"}
    except db.exceptions.DatabaseError as e:
        print(f"Database Error during registration: {e}")
        return {'success': False, 'error': f"Database error: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred during registration: {e}")
        return {'success': False, 'error': f"An unexpected error occurred: {e}"}
def Quick_Save(key, value):
    try:
        # Ensure the Firebase app is initialized
        if not firebase_admin._apps:
            initialize_firebase()  # Assuming initialize_firebase() is already defined in this module

        # Reference to the database
        ref = db.reference('/')
        
        # Setting the value in the database
        ref.child(key).set(value)
        print(f"Data saved successfully. Key: {key}, Value: {value}")
        return True
    except Exception as e:
        print(f"Error saving data to Firebase: {e}")
        return False
def search_database_and_auth_new(loginid):
    ref = db.reference('Users')
    all_users = ref.get()
    for uid, user in all_users.items():
        if user.get('Email') == loginid or user.get('Username') == loginid:
            return uid, user
    return None, None
def search_database_and_auth(**search_pairs):
    try:
        # Ensure the Firebase app is initialized
        if not firebase_admin._apps:
            initialize_firebase()  # Assuming initialize_firebase() is already defined in this module

        # Retrieve all data from the Realtime Database
        ref = db.reference('/')
        db_data = ref.get()

        # Retrieve all users from Firebase Auth
        all_users = auth.list_users().iterate_all()

        results = {
            'database': [],
            'auth': []
        }

        # Search in database
        for key, value in search_pairs.items():
            for db_key, db_value in db_data.items():
                if key in db_key and value == db_value:
                    results['database'].append({db_key: db_value})

        # Search in auth users
        for key, value in search_pairs.items():
            for user in all_users:
                user_info = {
                    'uid': user.uid,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'display_name': user.display_name
                }
                if key in user_info and value == str(user_info[key]):
                    results['auth'].append(user_info)

        return results
    except Exception as e:
        print(f"Error searching in Firebase: {e}")
        return None
    

from firebase_admin import exceptions
def portal_login():
    data = request.get_json()
    id_token = data.get('idToken')

    if not id_token:
        return jsonify({"error": "No ID token provided."}), 400

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        user = auth.get_user(uid)

        return jsonify({"success": True, "uid": user.uid, "email": user.email}), 200
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Invalid ID token."}), 401
    except exceptions.FirebaseError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
def load_json(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(data: dict, file_path: str) -> None:
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def get_value(data: dict, key_path: List[str]) -> Any:
    for key in key_path:
        data = data.get(key, {})
    return data if data else None

def set_value(data: dict, key_path: List[str], value: Any) -> bool:
    temp = data
    for key in key_path[:-1]:
        temp = temp.setdefault(key, {})
    temp[key_path[-1]] = value
    return True

# Example usage:
if __name__ == "__main__":
    # Define the path to your JSON file
    json_path = 'path_to_your_json_file.json'

    # Load the data
    data = load_json(json_path)

    # Get a value
    print(get_value(data, ['key1', 'subkey2']))

    # Set a new value
    if set_value(data, ['key1', 'subkey2'], 'new_value'):
        save_json(data, json_path)