from flask import Flask, send_file, request, jsonify,template_rendered
from flask import Flask, redirect, url_for,session
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
from pydub import AudioSegment
import base64
import time
import random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
import datetime


# Khởi tạo Flask Server Backend
app = Flask(__name__)
openai.api_key = "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"

# Apply Flask CORS
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

with open('f_key.json', 'r') as file:
    data_key = json.load(file)


if not firebase_admin._apps:
    cred = credentials.Certificate(data_key) 
    default_app = firebase_admin.initialize_app(cred)
else:
  firebase_admin.get_app()

db = firestore.client()

# Get a reference to the default Firebase Storage bucket
bucket = storage.bucket('reybo-af765.appspot.com')

# Upload a file to Firebase Storage
def upload_file(file_path, destination_path):
    blob = bucket.blob(destination_path)
    blob.upload_from_filename(file_path)


def check_account(user_name):
  folder_path = 'User 1/Data/Test/'

  # List all files in the folder
  files = bucket.list_blobs(prefix=folder_path)

  # Iterate over the files
  for file in files:
    if file.name.endswith('.json'):  # Filter JSON files
        # Download the JSON file to a local temporary file
        temp_file_path = 'temp.json'
        file.download_to_filename(temp_file_path)

        # Read the contents of the JSON file
        with open(temp_file_path, 'r') as json_file:
            json_data = json.load(json_file)
        if user_name == json_data['user_name']:
            return True
        # Delete the temporary file
        os.remove(temp_file_path)
  return False


def sign_in_by_account(user_name, password):
    folder_path = 'User 1/Data/Test/'

    # List all files in the folder
    files = bucket.list_blobs(prefix=folder_path)

    # Iterate over the files
    for file in files:
        if file.name.endswith('.json'):  # Filter JSON files
            # Download the JSON file to a local temporary file
            temp_file_path = 'temp.json'
            file.download_to_filename(temp_file_path)

            # Read the contents of the JSON file
            with open(temp_file_path, 'r') as json_file:
                json_data = json.load(json_file)

            if user_name == json_data['user_name'] and password == json_data['password']:
                # Delete the temporary file
                
                payload = {'value': json_data['public_key']}
                print(payload)
                response = requests.post('http://127.0.0.1:6868/api/pub-variable', json=payload)
                os.remove(temp_file_path)
                return True
    
            # Delete the temporary file
            os.remove(temp_file_path)

    return False

def encrypt_with_rsa_public_key(data, rsa_public_key):
    data_bytes = data.encode()  # Convert data to bytes
    encrypted_data = rsa_public_key.encrypt(
        data_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_data
def string_to_pem(string_content, file_path):
    with open(file_path, 'w') as file:
        file.write(string_content)

public_key_variable = None


@app.route('/api/pub-variable', methods=['GET'])
def get_pub_variable():
    global public_key_variable
    return jsonify({'public_key': public_key_variable})

@app.route('/api/pub-variable', methods=['POST'])
def set_pub_variable():
    global public_key_variable
    data = request.json
    public_key_variable = data['value']
    return jsonify({'message': 'Mutable variable set successfully'})

def sign_in_by_QR(image_path):
  # Load the QR image
  qr_image = Image.open(image_path)

  # Decode the QR code
  decoded = decode(qr_image)

  # Extract the data from the QR code
  if len(decoded) > 0:
    qr_data = decoded[0].data.decode("utf-8")
    #print(qr_data)
    folder_path = 'User 1/Data/Test/'

    # List all files in the folder
    files = bucket.list_blobs(prefix=folder_path)
    
    QR_data = json.loads(qr_data)
    for file in files:
      if file.name.endswith('.json'):  # Filter JSON files
        # Download the JSON file to a local temporary file
        temp_file_path = 'temp.json'
        file.download_to_filename(temp_file_path)

        # Read the contents of the JSON file
        with open(temp_file_path, 'r') as json_file:
            json_data = json.load(json_file)
        if QR_data["public_key"] == json_data['public_key']:
            return True
        # Delete the temporary file
        os.remove(temp_file_path)
    return False
  else:
    print("No QR code found in the image.")
    return False
global_answer = None
global_urls=None  
global_content=None
global_number=None
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/qr_login', methods=['GET'])
def qr_login():
    return render_template('qr_login.html')

@app.route('/signup', methods=['POST'])
def signup():
    

    user_name=request.form.get('email')
    password=request.form.get('password')
    public_key=request.form.get('publickey')
    if check_account(user_name):
        return jsonify({'success': False, 'message': 'User already exists'})

    temp = {"user_name": "", "password": "", "public_key": ""}
    temp["user_name"] = user_name
    temp["password"] = password
    temp["public_key"] = public_key
    file_path = "dataT.json"

    with open(file_path, "w") as file:
        # Write the dictionary as JSON data to the file
        json.dump(temp, file)

    # Generate a unique file name
    unique_filename = str(uuid.uuid4())

    # Append a file extension if needed
    file_name = unique_filename + ".json"
    upload_file(file_path, "User 1/Data/Test/{}".format(file_name))

    #return jsonify({'success': True, 'message': 'User signed up successfully'})
    return render_template('InputText.html')


@app.route('/signin/account', methods=['POST'])
def sign_in():
    # user_name = request.args.get('user_name')
    # password = request.args.get('password')
    user_name=request.form.get('email')
    password=request.form.get('password')
    if sign_in_by_account(user_name, password):
        response = requests.get('http://127.0.0.1:6868/api/gen-code')
        if response.status_code == 200:
            data = response.json()
            text = data['check_in']
            print(text)
            # Xử lý check_in theo ý muốn
            return render_template('message.html',text=text)
            
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})



@app.route('/signin/qr', methods=['POST'])
def sign_in_qr():
    # image_path = request.args.get('/static/json_qr_code.png')
    image_path=request.files['image-upload']
    #image_path='static/json_qr_code.png'
    if sign_in_by_QR(image_path):
        return render_template('InputText.html')
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    


@app.route('/api/answer', methods=['POST'])
def get_answer():
    global global_answer
    # Retrieve the question from the query parameters
    question = request.form.get('inputtext')

    # Generate the answer using the OpenAI GPT-3 API
    answer = generate_answer(question)
    global_answer = answer
    # Return the answer as a JSON response
   # return jsonify({'answer': answer})
   
 
    return render_template('EditContent.html', answer=answer)
   # return redirect(url_for('use_answer'))
def generate_answer(question):
    # Generate answer using OpenAI GPT-3 API
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Question: {question}\nAnswer:",
        max_tokens=1024,
    )

    # Extract answer from API response
    answer = response.choices[0]['text'].strip()

    # Return answer
    return answer

@app.route('/edit', methods=['POST'])
def edit_content():
    global global_content,global_number
    content=request.form.get('inputtext')
    number=int(request.form.get('number'))
    global_content=content
    global_number=number
    
    return  render_template('temp.html',content=content,number=number)
    

@app.route('/generate-images', methods=['POST'])
def generate_images_api():
#     # Get the text input from the request body
#     text_input = request.form.get('text_input')
#    # answer = requests.post('http://127.0.0.1:6868/api/answer').text

#     # Generate images based on the answer
#     images = generate_images(text_input)
#     # Generate images based on the answer
#     return jsonify({'image': images})
    image_urls = []
    global global_urls
    global global_number
    number=global_number
    for i in range(number):
        text_input = request.form.get(f'text_input{i}')
        images = generate_images(text_input)
        #image_urls.append(images)
        image_urls=image_urls+images
    global_urls=image_urls
    
    #return jsonify({'image_urls': image_urls})
    jsonfile=jsonify({'image_urls': image_urls})
    json_str=jsonfile.json
    
    print(json_str)
    
    return render_template('test.html',json_str=json_str  )
    #return jsonify({'image_urls': image_urls})
    #return redirect(url_for('generate_video'))
def generate_images(text_input):
    num_images = 1
    """
    Generates a list of images based on the given text input using the DALL-E 2.0 API.

    Parameters:
    text_input (str): The text input used to generate the images.
    num_images (int): The number of images to generate. Default is 5.

    Returns:
    List of images in PNG format.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai.api_key}'
    }

    data = {
        'model': 'image-alpha-001',
        'prompt': text_input,
        'num_images': num_images,
        'size': '512x512',
        'response_format': 'url'
    }

    response = requests.post('https://api.openai.com/v1/images/generations', headers=headers, data=json.dumps(data))
    response_json = response.json()
    while 'error' in response_json:
        time.sleep(20)
        response = requests.post('https://api.openai.com/v1/images/generations', headers=headers, data=json.dumps(data))
        response_json = response.json()
     
    # Extract image URLs from response
    image_urls = [result['url'] for result in response_json['data']]
    
    return list(image_urls)

@app.route('/api/other', methods=['GET'])
def use_answer():
    global global_answer  # Sử dụng biến toàn cục

    # Kiểm tra nếu có kết quả từ trước
    if global_answer is not None:
        # Sử dụng kết quả
        result = global_answer
        return jsonify({'result': result})
    else:
        # Trả về thông báo lỗi hoặc xử lý khác
        return jsonify({'error': 'Không có kết quả'})

@app.route('/process_images', methods=['POST'])
def process_images():
    selected_images = request.form['selectedImages']
    selected_images = json.loads(selected_images)
    return selected_images


@app.route('/generate-video', methods=['POST'])
def generate_video():
    # image_urls = request.args.getlist('image_urls')
    # answer = request.args.get('answer')
    global global_answer 
    # global global_urls
    # image_urls=global_urls
    selected_images = request.form['selectedImages']
    selected_images = json.loads(selected_images)
    image_urls=selected_images
    answer=global_answer
    # image_urls=["https://oaidalleapiprodscus.blob.core.windows.net/private/org-nzb6rPHoC85FwWwYDFEV20Ni/user-S03qEwb5N3IWVZwrt7rdguSo/img-TFv4Z5BF1THs4ZDEErYnK2HG.png?st=2023-06-11T08%3A18%3A46Z&se=2023-06-11T10%3A18%3A46Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-10T20%3A41%3A06Z&ske=2023-06-11T20%3A41%3A06Z&sks=b&skv=2021-08-06&sig=uj8kF/Hln1%2BdaFZF3XzKjsba3qPQLDvOpAVkazCD1Ug%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-nzb6rPHoC85FwWwYDFEV20Ni/user-S03qEwb5N3IWVZwrt7rdguSo/img-vQN18HszEKfTaDK9QK02KtMr.png?st=2023-06-11T08%3A18%3A53Z&se=2023-06-11T10%3A18%3A53Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-10T20%3A42%3A37Z&ske=2023-06-11T20%3A42%3A37Z&sks=b&skv=2021-08-06&sig=loEGXJqQ%2B9QFlqeyXGs5phFUXaIkCbr56v3DBMvUrSQ%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-nzb6rPHoC85FwWwYDFEV20Ni/user-S03qEwb5N3IWVZwrt7rdguSo/img-NrjFle27ivVSLOWWhU8bdSnW.png?st=2023-06-11T08%3A19%3A00Z&se=2023-06-11T10%3A19%3A00Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-10T20%3A49%3A16Z&ske=2023-06-11T20%3A49%3A16Z&sks=b&skv=2021-08-06&sig=Lo%2BAfKZvVBgqVuG1tcBFAl25C6pmEW70GimSJUQst3Y%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-nzb6rPHoC85FwWwYDFEV20Ni/user-S03qEwb5N3IWVZwrt7rdguSo/img-NIJNDjNiXVJKseuXSiDNvQce.png?st=2023-06-11T08%3A19%3A07Z&se=2023-06-11T10%3A19%3A07Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-10T20%3A39%3A26Z&ske=2023-06-11T20%3A39%3A26Z&sks=b&skv=2021-08-06&sig=3QXbZUTCk4QRg9EQW8JQnp486xgTiiLJq8Xs1pEZccw%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-nzb6rPHoC85FwWwYDFEV20Ni/user-S03qEwb5N3IWVZwrt7rdguSo/img-G0azxsXmXcDwJVHQkHPrG17L.png?st=2023-06-11T08%3A19%3A24Z&se=2023-06-11T10%3A19%3A24Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-10T20%3A39%3A40Z&ske=2023-06-11T20%3A39%3A40Z&sks=b&skv=2021-08-06&sig=qoqpGQz2/GsJsrNjWaSfrpE%2BVB%2BDj76vv4Kb48PCt8I%3D"]
    # answer="Women in Vietnam play an important role in society. They are active participants in the country's development and progress, particularly in the fields of healthcare, education, business and government. In recent years, women have been playing a larger role in leadership positions, with a number of female politicians taking up high-profile positions in the government. Vietnam has also seen a number of initiatives that focus particularly on empowering women, such as the introduction of cash transfers as well as job training programs."
    tts = gTTS(text=answer, lang="en")
    audio_path = 'text_audio.mp3'
    tts.save(audio_path)

    # Load the audio file
    audio_clip = mp.AudioFileClip(audio_path)

    # Create a list of video clips from the image URLs
    #video_clips = [ImageSequenceClip([image_url], durations=[audio_clip.duration]) for image_url in image_urls]
    video_clips = [ImageSequenceClip([image_url], durations=[audio_clip.duration/ len(image_urls)]) for image_url in image_urls]
    # Concatenate the video clips
    final_clip = concatenate_videoclips(video_clips)

    # Set the audio for the final clip
    final_clip = final_clip.set_audio(audio_clip)
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

    # Set the output file path
    output_path = os.path.join(static_dir, 'output.mp4')

    # Write the final clip to the output file
    final_clip.write_videofile(output_path, codec='libx264', fps=24)
    
    return render_template('video.html')
   
def encrypt_file(input_file, output_file, key):
    with open(input_file, 'rb') as file_in, open(output_file, 'wb') as file_out:
        data = file_in.read()
        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(data)
        file_out.write(encrypted_data)

def decrypt_file(input_file, output_file, key):
    with open(input_file, 'rb') as file_in, open(output_file, 'wb') as file_out:
        encrypted_data = file_in.read()
        cipher = Fernet(key)
        decrypted_data = cipher.decrypt(encrypted_data)
        file_out.write(decrypted_data)

def split_file(input_file, file1, file2, split_ratio):
    # Read the input file
    with open(input_file, 'rb') as file:
        data = file.read()

    # Calculate the split point based on the split ratio
    split_point = int(len(data) * split_ratio)

    # Split the data into two parts
    data1 = data[:split_point]
    data2 = data[split_point:]

    # Write the data to the output files
    with open(file1, 'wb') as file:
        file.write(data1)
    with open(file2, 'wb') as file:
        file.write(data2)

def merge_files(file1, file2, output_file):
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2, open(output_file, 'wb') as output:
        output.write(f1.read())
        output.write(f2.read())


@app.route('/encrypt', methods=['POST'])
def encrypt_endpoint():
    #input_file = request.args.get('input_file')
    file_name1 = request.form.get('filename1')
    file_name2 = request.form.get('filename2')
    # file_name1='test1.mp4'
    # file_name2='test2.mp4'
    file1 = 'file1.mp4'
    file2 = 'file2.mp4'
    encryptTest = 'encryptTest.mp4'
    key = request.form.get('key')
    #key='BZ93_f81FnUhKTSus_uia328KqH0zKej5Ds4dQoIdg0='

    # Convert the string to bytes
    key_bytes = key.encode('utf-8')

    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

    # Set the output file path
    input_file = os.path.join(static_dir, 'output.mp4')

    # input_file = 'output.mp4'
    split_file(input_file, file1, file2, 0.05)
    upload_file(file2, "User 1/Data/Test/{}".format(file_name2))

    encrypt_file(file1, encryptTest, key_bytes)
    upload_file(encryptTest, "User 1/Data/Test/{}".format(file_name1))

    print(file_name1)
    print(file_name2)
    print(key)

    response = {
        'message': 'File encrypted successfully.',
    }
    return jsonify(response)

def read_mp4_from_firebase(filename, output_path):
  blob = bucket.blob("User 1/Data/Test/{}".format(filename))
  url = blob.generate_signed_url(
    version='v4',
    expiration=datetime.timedelta(minutes=5),  # Set the desired expiration time
    method='GET'
  )
  response = requests.get(url)
  if response.status_code == 200:
    with open(output_path, 'wb') as f:
        f.write(response.content)
    print("MP4 file downloaded successfully.")
  else:
    print("Failed to download the MP4 file.")
@app.route('/input/decrypt', methods=['GET'])
def decrypt_video():
    return render_template('decrypt_video.html')

@app.route('/decrypt', methods=['POST'])
def decrypt_endpoint():
    file_name1 = request.form.get('filename1')
    file_name2 = request.form.get('filename2')
    key = request.form.get('key')
    #file_name1='test1.mp4'
    #file_name2='test2.mp4'
    # file1 = 'file1.mp4'
    # file2 = 'file2.mp4'
    file3 = 'F1.mp4'
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

    # Set the output file path
    decryptTest = os.path.join(static_dir, 'decryptTest.mp4')
    #decryptTest = 'decryptTest.mp4'
    read_mp4_from_firebase(file_name1,file_name1)
    read_mp4_from_firebase(file_name2,file_name2)
    #key = request.args.get('key')
    #key='BZ93_f81FnUhKTSus_uia328KqH0zKej5Ds4dQoIdg0='

    # Convert the string to bytes
    key_bytes = key.encode('utf-8')

    decrypt_file(file_name1,file3,key_bytes)
    merge_files(file3,file_name2,decryptTest)

    response = {
        'message': 'File decrypted successfully.'
    }
    #return jsonify(response)
    return render_template('save_video.html')
# Mutable variable
mutable_variable = None

@app.route('/api/mutable-variable', methods=['GET'])
def get_mutable_variable():
    global mutable_variable
    return jsonify({'mutable_variable': mutable_variable})

@app.route('/api/mutable-variable', methods=['POST'])
def set_mutable_variable():
    global mutable_variable
    data = request.json
    mutable_variable = data['value']
    return jsonify({'message': 'Mutable variable set successfully'})

@app.route('/api/gen-code', methods=['GET'])
def generate_check_in(): 
  # Generate a random 4-digit number
  random_number = random.randint(1000, 9999)
 
  response = requests.get('http://127.0.0.1:6868/api/pub-variable')
  if response.status_code == 200:
    data = response.json()
    #print(data['public_key'])
  
  # Create an RSA cipher object with the public key
  #cipher_rsa = PKCS1_OAEP.new(public_key)
  key_string = data['public_key']
  cipher_rsa = serialization.load_pem_public_key(key_string.encode(), backend=default_backend())
  #print(type(cipher_rsa))
  # Encrypt the random number
#   encrypted_data = cipher_rsa.encrypt(str(random_number).encode())

#   # Base64 encode the encrypted data
#   encoded_data = base64.urlsafe_b64encode(encrypted_data)

#   # Convert the encoded data to a string
 # encrypted_text = encoded_data.decode()
  encrypted_text=encrypt_with_rsa_public_key(str(random_number),cipher_rsa)


  payload = {'value': random_number}
  response = requests.post('http://127.0.0.1:6868/api/mutable-variable', json=payload)

# Check the response status code
  if response.status_code == 200:
    data = response.json()
    message = data['message']
        # Process the response as needed
    print(message)
  else:
        # Handle the error response
    print('Error:', response.status_code)
  return jsonify({'check_in': str(encrypted_text)})

@app.route('/api/check-in', methods=['POST'])
def check_in():
    #code = request.args.get('code')
    code=request.form.get('inputcode')
    response = requests.get('http://127.0.0.1:6868/api/mutable-variable')

    # Check the response status code
    if response.status_code == 200:
        data = response.json()
        mutable_variable = data['mutable_variable']
        # Process the mutable variable as needed
        print(mutable_variable)
    else:
        # Handle the error response
        print('Error:', response.status_code)
    if(int(code) == mutable_variable):
        return render_template('InputText.html')
    else:
        return jsonify({'success': False, 'message': 'Invalid code'})




# Start Backend
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='6868')