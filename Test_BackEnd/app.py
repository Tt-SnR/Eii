from flask import Flask, send_file, request, jsonify,template_rendered
from flask import Flask, redirect, url_for
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
import openai
import json
import requests
from moviepy.editor import ImageSequenceClip
from gtts import gTTS
import os
import moviepy.editor as mp
from moviepy.editor import ImageSequenceClip, concatenate_videoclips
from cryptography.fernet import Fernet
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from firebase_admin import firestore
import firebase
import uuid
from pyzbar.pyzbar import decode
from PIL import Image
import base64


app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('qr_login.html')


@app.route('/login', methods=['POST'])
def login():
    # Get the image file from the request
    image_file = request.files['image']
    
    # Process the image file, e.g., decode the QR code
    
    # Return a response to the client
    response = {'message': 'Login successful'}
    return 'Thanh cong'

if __name__ == '__main__':
    app.run()
