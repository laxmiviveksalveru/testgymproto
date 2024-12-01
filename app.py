import math
from flask import Flask, redirect, render_template, request, make_response, session, abort, jsonify, url_for
import secrets
from functools import wraps
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import timedelta
import os
import json
import torch
from PIL import Image
from torchvision import transforms
from transformers import ViTForImageClassification, ViTImageProcessor
from safetensors.torch import load_file
from werkzeug.utils import secure_filename
from cloudinary.uploader import upload as cloudinary_upload
import cloudinary  
from dotenv import load_dotenv
import requests
from gradio_client import Client, handle_file

load_dotenv()

app = Flask(__name__)

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME_1'),
    api_key=os.getenv('CLOUDINARY_API_KEY_1'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET_1')
)

# Configure accessory Cloudinary using environment variables
cloudinary_accessory_config = cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME_2'),
    api_key=os.getenv('CLOUDINARY_API_KEY_2'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET_2')
)

app.secret_key = os.getenv('SECRET_KEY')

# Configure session cookie settings
app.config['SESSION_COOKIE_SECURE'] = True  # Ensure cookies are sent over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Adjust session expiration as needed
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Can be 'Strict', 'Lax', or 'None'
app.config['SESSION_TYPE'] = 'filesystem'

  # Firebase Admin SDK setup
auth_cred = credentials.Certificate("firebase-auth.json")
default_app = firebase_admin.initialize_app(auth_cred)

# Set up Firestore and other services using the main Firebase app instance
db = firestore.client(app=default_app)

# Load additional credentials for specific operations
trainer_cred = credentials.Certificate("firebase-database.json")
trainer_app = firebase_admin.initialize_app(trainer_cred, name='trainer_app')

trainer_db = firestore.client(app=trainer_app)  # Use the same app for Firestore

accessory_cred = credentials.Certificate("firebase-accessories.json")
accessory_app = firebase_admin.initialize_app(accessory_cred, name='accessory_app')
accessory_db = firestore.client(app=accessory_app)  # Use the same app for Firestore

class_names = [
    "elliptical", "barbell", "crossover_cable", "dumbell", "flat_benchpress", "flat_bench",
    "lat_pull_down", "leg_extension", "legpress", "pec_desk_fly", "shoulder_press",
    "sitted_row_machine", "smith_machine", "static_cycle", "tread_mill"
]

# Gradio Client Initialization
gradio_client = Client("viveksalveru/vit-gym-classifier")

# Function to get muscles and tutorial links
def get_muscles_and_tutorial(predicted_class_name):
    """
    Returns a detailed list of muscle groups and associated video tutorials 
    for specific gym equipment, designed for beginners and fitness enthusiasts.
    """
    muscles_data = {
        "elliptical": {
            "Targeted Muscles": ["Quads", "Hamstrings", "Glutes", "Calves", "Cardio"],
            "Videos": {
                "Proper Elliptical Form": "https://youtu.be/oHk2Lucm0qE?si=17H91L1UXioHInHo",
                "Fat Burn Cardio Routine": "https://youtu.be/video_elliptical_cardio"
            }
        },
        "barbell": {
            "Targeted Muscles": ["Chest (Upper, Middle, Lower)", "Triceps", "Shoulders"],
            "Videos": {
                "Barbell Bench Press (Chest)": "https://youtu.be/video_barbell_bench_press",
                "Overhead Shoulder Press": "https://youtu.be/video_barbell_shoulder_press",
                "Barbell Skull Crushers (Triceps)": "https://youtu.be/video_barbell_triceps"
            }
        },
        "crossover_cable": {
            "Targeted Muscles": ["Chest (Upper, Inner)", "Rear Delts", "Biceps"],
            "Videos": {
                "Cable Crossover for Inner Chest": "https://youtu.be/video_cable_inner_chest",
                "Face Pulls (Rear Delts)": "https://youtu.be/video_face_pulls",
                "Cable Bicep Curls": "https://youtu.be/video_cable_bicep_curl"
            }
        },
        "dumbell": {
            "Targeted Muscles": ["Biceps", "Triceps", "Shoulders", "Chest"],
            "Videos": {
                "Dumbbell Bicep Curls": "https://youtu.be/video_dumbbell_curls",
                "Dumbbell Tricep Kickbacks": "https://youtu.be/video_dumbbell_triceps",
                "Dumbbell Chest Press": "https://youtu.be/video_dumbbell_chest_press"
            }
        },
        "flat_benchpress": {
            "Targeted Muscles": ["Chest (Middle)", "Triceps", "Front Delts"],
            "Videos": {
                "Flat Bench Press (Chest)": "https://youtu.be/video_flat_benchpress",
                "Triceps Activation on Bench Press": "https://youtu.be/video_bench_triceps"
            }
        },
        "flat_bench": {
            "Targeted Muscles": ["Chest (Stretch)", "Core"],
            "Videos": {
                "Dumbbell Flyes for Chest Stretch": "https://youtu.be/video_flat_bench_flyes",
                "Ab Crunches on Bench": "https://youtu.be/video_bench_abs_crunches"
            }
        },
        "lat_pull_down": {
            "Targeted Muscles": ["Lats", "Biceps", "Rear Delts"],
            "Videos": {
                "Wide Grip Lat Pulldown": "https://youtu.be/video_lat_pulldown_wide",
                "Close Grip Pulldown for Biceps": "https://youtu.be/video_lat_biceps_pulldown"
            }
        },
        "leg_extension": {
            "Targeted Muscles": ["Quads"],
            "Videos": {
                "Leg Extensions for Strong Quads": "https://youtu.be/video_leg_extension",
                "Perfect Form for Leg Extension": "https://youtu.be/video_leg_form"
            }
        },
        "legpress": {
            "Targeted Muscles": ["Quads", "Glutes", "Hamstrings", "Calves"],
            "Videos": {
                "How to Leg Press Safely": "https://youtu.be/video_legpress_safe",
                "Calf Extensions on Leg Press": "https://youtu.be/video_legpress_calves"
            }
        },
        "pec_desk_fly": {
            "Targeted Muscles": ["Inner Chest"],
            "Videos": {
                "Pec Deck Fly for Inner Chest": "https://youtu.be/video_pec_inner",
                "Stretching the Chest on Pec Deck": "https://youtu.be/video_pec_stretch"
            }
        },
        "shoulder_press": {
            "Targeted Muscles": ["Shoulders (Front, Side)", "Traps"],
            "Videos": {
                "Seated Overhead Shoulder Press": "https://youtu.be/video_seated_shoulder_press",
                "Dumbbell Shrugs for Traps": "https://youtu.be/video_traps_shrugs"
            }
        },
        "sitted_row_machine": {
            "Targeted Muscles": ["Middle Back", "Lats", "Rear Delts"],
            "Videos": {
                "Perfect Form for Seated Rows": "https://youtu.be/video_seated_row_form",
                "Row Variations for Lats": "https://youtu.be/video_lats_row"
            }
        },
        "smith_machine": {
            "Targeted Muscles": ["Quads", "Glutes", "Chest (Incline)", "Shoulders"],
            "Videos": {
                "Smith Machine Squats for Legs": "https://youtu.be/video_smith_squats",
                "Incline Bench Press on Smith Machine": "https://youtu.be/video_smith_incline"
            }
        },
        "static_cycle": {
            "Targeted Muscles": ["Quads", "Calves", "Cardio"],
            "Videos": {
                "Stationary Cycle Warmup": "https://youtu.be/video_cycle_warmup",
                "Fat Burning Cardio Routine": "https://youtu.be/video_cycle_cardio"
            }
        },
        "tread_mill": {
            "Targeted Muscles": ["Cardio", "Glutes", "Quads"],
            "Videos": {
                "Proper Running Form on Treadmill": "https://youtu.be/video_treadmill_running",
                "Treadmill Incline Walk for Glutes": "https://youtu.be/video_treadmill_incline"
            }
        }
    }
    data = muscles_data.get(predicted_class_name, {"info": "No specific muscle data available."})
    return {
        "muscles": data.get("Targeted Muscles", []),
        "tutorials": data.get("Videos", {})
    }
# Prediction route
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    temp_file_path = "temp_upload.jpg"
    file.save(temp_file_path)

    try:
        # Use Gradio Client for prediction
        result = gradio_client.predict(
            image=handle_file(temp_file_path),
            api_name="/predict"
        )
        predicted_class_index = result.get('class', 0)
        confidence = result.get('confidence', 0.0)
    except Exception as e:
        print(f"Error in Gradio Client: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

    predicted_class_name = class_names[predicted_class_index]
    data = get_muscles_and_tutorial(predicted_class_name)

    return render_template(
        'result.html',
        predicted_class=predicted_class_name,
        confidence=round(confidence, 4),
        muscles=data["muscles"],
        tutorials=data["tutorials"]
    )



# Function to get muscles and tutorial links

# Decorator for routes that require authentication
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        else:
            return f(*args, **kwargs)
    return decorated_function

import logging

from datetime import datetime, timedelta

@app.route('/auth', methods=['POST'])
def authorize():
    token = request.headers.get('Authorization')
    if not token:
        logging.error("Authorization header is missing")
        return "Unauthorized: No Authorization header", 401
    elif not token.startswith('Bearer '):
        logging.error("Authorization header does not start with 'Bearer '")
        return "Unauthorized: Invalid token format", 401

    token = token[7:]  # Strip off 'Bearer ' to get the actual token
   

    try:
        # Decode the token
        decoded_token = auth.verify_id_token(token)
        issued_at = datetime.utcfromtimestamp(decoded_token['iat'])  # Token issued at time
        current_time = datetime.utcnow()  # Current server time
        time_difference = (current_time - issued_at).total_seconds()

        # Allow a 5-second buffer for time synchronization
        if time_difference < -5:
            logging.error(f"Token used too early. Time difference: {time_difference} seconds")
            return "Unauthorized: Token used too early", 401

        user_email = decoded_token.get('email')
        session['user_email'] = user_email  # Store user email in session
        session['user'] = decoded_token  # Store entire user data in session

        # Debugging: Print user and email
        print(f"Decoded User: {decoded_token}")
        print(f"User Email: {user_email}")

        return redirect(url_for('dashboard'))

    except Exception as e:
        logging.error(f"Token verification failed: {e}")
        return "Unauthorized: Token verification failed", 401

#####################
""" Public Routes """
admin_email = os.getenv('ADMIN_EMAIL')
@app.route('/')
def home():
    accessories_ref = accessory_db.collection('accessories')
    accessories_docs = accessories_ref.stream()
    
    accessories = []
    for doc in accessories_docs:
        data = doc.to_dict()
        print("Retrieved document data:", data)  # This will print the document data
        accessories.append(data)
    
    return render_template('home.html', accessories=accessories)


@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signup')
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/reset-password')
def reset_password():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('forgot_password.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response
@app.route('/upload_trainer', methods=['GET', 'POST'])
def upload_trainer():
    # Check if the user is logged in and their email matches the admin email
    user_email = session.get('user_email')
    if user_email != admin_email:
        return render_template('upload_trainer.html', message="Access denied. Only admins can upload trainers.", success=False)

    if request.method == 'GET':
        return render_template('upload_trainer.html')  # Provide a form page for GET requests

    # POST request handling
    try:
        name = request.form.get('name')
        if not name:
            return render_template('upload_trainer.html', message="Name is required", success=False)

        country = request.form['country']
        city = request.form['city']
        language = request.form['language']
        timing = request.form['timing']
        price = int(request.form['price'])
        contact = request.form['contact']
        instagram = request.form['instagram']
        experience = int(request.form['experience'])
        rating = int(request.form['rating'])

        # Convert language input to a list of lowercase values
        languages = [lang.strip().lower() for lang in language.split(",")]

        # Upload photo to Cloudinary
        photo = request.files['photo']
        photo_url = cloudinary_upload(photo, folder="trainers")['secure_url']

        # Upload certificate to Cloudinary
        certificate = request.files['certificate']
        certificate_url = cloudinary_upload(certificate, folder="certificates")['secure_url']

        trainer_data = {
            "name": name,
            "country": country,
            "city": city,
            "language": languages,  # Store as list
            "timing": timing,
            "price": price,
            "contact": contact,
            "instagram": instagram,
            "experience": experience,
            "rating": rating,
            "photo_url": photo_url,
            "certificate_url": certificate_url
        }

        trainer_db.collection('trainers').add(trainer_data)
        return render_template('upload_trainer.html', message="Trainer uploaded successfully!", success=True)

    except Exception as e:
        return render_template('upload_trainer.html', message=f"Error: {str(e)}", success=False)

@app.route('/view_trainers', methods=['GET'])
def view_trainers():
    # Default page and per-page values
    page = int(request.args.get('page', 1))
    per_page = 10

    # Extract filter values from request
    filters = {
        "name": request.args.get('name'),
        "country": request.args.get('country'),
        "city": request.args.get('city'),
        "language": request.args.get('language'),
        "min_experience": request.args.get('min_experience'),
        "max_experience": request.args.get('max_experience'),
        "min_price": request.args.get('min_price'),
        "max_price": request.args.get('max_price'),
        "rating": request.args.get('rating')
    }

    # Initialize the query
    query = trainer_db.collection('trainers')

    # Apply filters to the query
    for field, value in filters.items():
        if value:
            if field == "min_experience":
                query = query.where("experience", ">=", int(value))
            elif field == "max_experience":
                query = query.where("experience", "<=", int(value))
            elif field == "min_price":
                query = query.where("price", ">=", float(value))
            elif field == "max_price":
                query = query.where("price", "<=", float(value))
            elif field == "rating":
                query = query.where("rating", ">=", float(value))
            elif field == "language":
                # Handle language inclusivity
                query = query.where("language", "array_contains_any", [value.lower()])
            else:
                # Case-insensitive matching for name, country, city
                query = query.where(field, "==", value.lower())

    # Fetch trainers from the query
    trainers = query.get()
    trainers = [trainer.to_dict() for trainer in trainers]  # Convert documents to dicts

    # Pagination logic
    total_trainers = len(trainers)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_trainers = trainers[start:end]
    total_pages = math.ceil(total_trainers / per_page)

    # Render the template
    return render_template(
        'view_trainer.html',
        trainers=paginated_trainers,
        current_page=page,
        total_pages=total_pages,
        prev_page=page - 1 if page > 1 else None,
        next_page=page + 1 if page < total_pages else None,
        pages=range(1, total_pages + 1)
    )



@app.route('/upload_accessory', methods=['GET', 'POST'])
def upload_accessory():
    # Check if the user is logged in and their email is the admin email
    user_email = session.get('user_email')  # Assuming user's email is stored in the session
    if not user_email or user_email !=admin_email:
        return "Unauthorized access! Only admins can upload accessories.", 403

    if request.method == 'POST':
        # Extract form data
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '').strip()
        description = request.form.get('description', '').strip()
        link = request.form.get('link', '').strip()

        # Validate form data
        if not name or not price or not description or not link:
            return "All fields are required!"

        # Ensure that the image is included in the request
        if 'image' not in request.files:
            return "No image file part"
        
        image = request.files['image']
        
        if image.filename == '':
            return "No selected file"
        
        # Secure the filename and upload image to Cloudinary
        try:
            image_url = cloudinary_upload(image, folder="accessories")['secure_url']
        except Exception as e:
            return f"Error uploading image: {str(e)}"

        # Accessory data to store in Firestore
        accessory_data = {
            "name": name,
            "price": price,
            "description": description,
            "link": link,
            "image_url": image_url
        }

        try:
            # Store the accessory data in Firestore
            accessory_db.collection('accessories').add(accessory_data)
        except Exception as e:
            return f"Error storing data in Firestore: {str(e)}"
        
        return redirect(url_for('accessory_success_page'))

    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="text" name="name" placeholder="Accessory Name" required><br>
        <input type="text" name="price" placeholder="Price" required><br>
        <textarea name="description" placeholder="Description" required></textarea><br>
        <input type="text" name="link" placeholder="Product Link" required><br>
        <input type="file" name="image" required><br>
        <button type="submit">Upload Accessory</button>
    </form>
    '''

# Example route to set session for testing purposes



@app.route('/accessory_success')
def accessory_success_page():
    return "Accessory uploaded successfully!"
##############################################
""" Private Routes (Require authorization) """


@app.route('/accessories')
def accessories():
    accessories_data = []
    try:
        accessories_ref = accessory_db.collection('accessories')
        docs = accessories_ref.stream()
        
        for doc in docs:
            accessories_data.append(doc.to_dict())
        print(accessories_data)  # Debug: print data to console
    except Exception as e:
        print(f"Error retrieving accessories data: {e}")  # Debug: print error message
        return "Error retrieving accessories data, please try again later."

    return render_template('accessories.html', accessories=accessories_data)

@app.route('/calculate-fat', methods=['POST'])
def calculate_fat():
    data = request.json
    gender = data.get('gender')
    height = float(data.get('height'))
    neck = float(data.get('neck'))
    waist = float(data.get('waist'))
    hip = float(data.get('hip')) if data.get('hip') else None

    if not height or not neck or not waist or (gender == 'female' and hip is None):
        return jsonify({'error': 'Please fill in all required fields.'}), 400

    if gender == 'male':
        body_fat_percentage = 495 / (1.0324 - 0.19077 * (waist - neck) + 0.15456 * height) - 450
    else:
        body_fat_percentage = 495 / (1.29579 - 0.35004 * (waist + hip - neck) + 0.221 * height) - 450

    body_fat_percentage = round(body_fat_percentage, 2)

    # Determine fat category
    if gender == 'male':
        if body_fat_percentage < 6:
            fat_category = 'Essential Fat'
        elif body_fat_percentage < 14:
            fat_category = 'Athlete'
        elif body_fat_percentage < 18:
            fat_category = 'Fitness'
        elif body_fat_percentage < 25:
            fat_category = 'Average'
        else:
            fat_category = 'Obese'
    else:
        if body_fat_percentage < 14:
            fat_category = 'Essential Fat'
        elif body_fat_percentage < 21:
            fat_category = 'Athlete'
        elif body_fat_percentage < 25:
            fat_category = 'Fitness'
        elif body_fat_percentage < 32:
            fat_category = 'Average'
        else:
            fat_category = 'Obese'

    # Suggest diet plan
    if fat_category in ['Essential Fat', 'Athlete']:
        diet_plan = 'Maintain your fitness with a balanced diet and proper hydration.'
    elif fat_category == 'Fitness':
        diet_plan = 'Focus on high-protein, nutrient-rich foods to maintain your level.'
    elif fat_category == 'Average':
        diet_plan = 'Incorporate a calorie-controlled, nutrient-dense diet with exercise.'
    else:
        diet_plan = 'Consult a healthcare provider for a personalized plan to reduce body fat.'

    return jsonify({
        'body_fat_percentage': body_fat_percentage,
        'fat_category': fat_category,
        'diet_plan': diet_plan
    })

@app.route('/bodyfat')
def bodyfat():
    return render_template('bodyfat.html')

@app.route('/dashboard')
@auth_required
def dashboard():
    accessories_ref1 = accessory_db.collection('accessories')
    accessories_docs1 = accessories_ref1.stream()
    
    accessories1 = []
    for doc1 in accessories_docs1:
        data1= doc1.to_dict()
        print("Retrieved document data:", data1)  # This will print the document data
        accessories1.append(data1)
    
    
    return render_template('dashboard.html' , accessories1=accessories1,admin_email=admin_email)

diet_plans = {
    'fat_loss': {
        'macros': 'High protein, low carb, moderate fat. Macronutrient Breakdown:Protein: 30%,Carbohydrates: 40%,Fat: 30%',
        'meals': {
            'Breakfast': 'Scrambled egg whites, avocado, whole grain toast, black coffee/green tee.',
            'Snack': 'Greek yogurt with berries, almonds.',
            'Lunch': 'Grilled chicken breast, quinoa, steamed broccoli',
            'Snack2': 'Whey protein shake, an apple.',
            'Dinner': 'Baked salmon, sweet potato, sautéed spinach.',
            'tip': 'add probiotics and fibers to diet,drink sufficient water',
            'Evening': 'Herbal tea.',
            'antioxidants':"blue berries,stawberries,pomegranates,kiwis,citrus fruit,leaf greens vegetables,if recommended add garlic/ginger with food"
        },'protein': {'According to ':'World Health Organization (WHO), Dietary Guidelines for Americans, and sports nutrition research.',
            'Protein Intake (grams)': ' Body Weight (kg) × Protein Requirement (g/kg)',
                     'Based on Goals and Activity':'Optimal Protein Intake Ranges ',
                    'Sendentary(minial activity)':'0.8-1.0g/kg',
                    'moderate activity(3-5days/week)':'1.2–1.6 g/kg',
                    'High Activity':'1.6–2.2 g/kg',
                    'Weight loss':'1.6-2.4g/kg',
                    'Weight Gain/Muscle Gain':'1.6–2.2 g/kg',
                    ' Weight Gain example':'Protein = 70 × 1.8 = 126 g per day',
                    'Weight loss example':'Protein = 70 × 2.0 = 140 g per day',
                    'Weight Maintenance example':'Protein = 70 × 1.4 = 98 g per day'
                    }
    },
    'muscle_gain': {
        'macros': 'High protein, higher carb, moderate fat.Macronutrient Breakdown:Protein: 35%,Carbohydrates: 45%,Fat: 20%',
        'meals': {
            'Breakfast': 'Oats with whey protein, milk, almond butter, banana,1 glass of fresh orange juice or a glass of buttermilk',
            'Snack': 'Protein smoothie (whey, spinach, berries, flaxseeds).',
            'Lunch': 'brown rice, avocado, mixed salad.',
            'Snack2': 'Cottage cheese, pumpkin seeds, and dried fruit.',
            'Dinner': 'Chinken, roasted vegetables, quinoa.',
            'Evening': 'whey protein or eggs,sweet potatoes',
            'tip': 'add probiotics and fibers to diet,drink sufficient water, if needed add fish oil,bananas',
            'antioxidants':"blue berries,stawberries,pomegranates,,kiwis,citrus fruit,leaf greens vegetables,if recommended add garlic/ginger with food"

        },'protein': {'According to ':'World Health Organization (WHO), Dietary Guidelines for Americans, and sports nutrition research.',
            'Protein Intake (grams)': ' Body Weight (kg) × Protein Requirement (g/kg)',
                     'Based on Goals and Activity':'Optimal Protein Intake Ranges ',
                    'Sendentary(minial activity)':'0.8-1.0g/kg',
                    'moderate activity(3-5days/week)':'1.2–1.6 g/kg',
                    'High Activity':'1.6–2.2 g/kg',
                    'Weight loss':'1.6-2.4g/kg',
                    'Weight Gain/Muscle Gain':'1.6–2.2 g/kg',
                    ' Weight Gain example':'Protein = 70 × 1.8 = 126 g per day',
                    'Weight loss example':'Protein = 70 × 2.0 = 140 g per day',
                    'Weight Maintenance example':'Protein = 70 × 1.4 = 98 g per day'
                    }
    },
    'performance': {
        'macros': 'Moderate protein, high carb, moderate fat.',
        'meals': {
            'Breakfast': 'dosa or idli/scrambled eggs,black coffie',
            'Snack': 'Protein bar, mixed fruit.',
            'Lunch': 'Grilled chicken, pasta with pesto, balanced amount of rice ,a side of greens',
            'Snack2': 'nuts,milk,bananas',
            'Dinner': 'Grilled fish, baked potato, steamed veggies.',
            'Evening': 'Hydration with electrolytes, and a small carb-based snack.',
            'tip': 'add probiotics and fibers to diet,drink sufficient water, if needed add fish oil ,if recommended add garlic/ginger with food',
            'antioxidants':"blue berries,stawberries,pomegranates,kiwis,citrus fruit,leaf greens vegetables,"

        },'protein': {'According to ':'World Health Organization (WHO), Dietary Guidelines for Americans, and sports nutrition research.',
            'Protein Intake (grams)': ' Body Weight (kg) × Protein Requirement (g/kg)',
                     'Based on Goals and Activity':'Optimal Protein Intake Ranges ',
                    'Sendentary(minial activity)':'0.8-1.0g/kg',
                    'moderate activity(3-5days/week)':'1.2–1.6 g/kg',
                    'High Activity':'1.6–2.2 g/kg',
                    'Weight loss':'1.6-2.4g/kg',
                    'Weight Gain/Muscle Gain':'1.6–2.2 g/kg',
                    ' Weight Gain example':'Protein = 70 × 1.8 = 126 g per day',
                    'Weight loss example':'Protein = 70 × 2.0 = 140 g per day',
                    'Weight Maintenance example':'Protein = 70 × 1.4 = 98 g per day'
                    }
    },
    'recovery': {
        'macros': 'Moderate protein, high carb, moderate fat.',
        'meals': {
            'Breakfast': 'Smoothie with protein powder, fruits, spinach, and chia seeds.',
            'Snack': 'Banana and a handful of nuts.',
            'Lunch': 'Chicken and vegetable stir fry with brown rice,tofu/low fat yogurt',
            'Snack2': 'Cottage cheese with fruit.',
            'Dinner': 'lean red meat fry with bell peppers/chicken, quinoa, and avocado.',
            'Evening': 'Anti-inflammatory foods like turmeric milk or ginger tea.',
             'tip': 'add probiotics and fibers to diet,drink sufficient water, if needed add fish oil ,sweet potato,if recommended add garlic/ginger with food',
            'antioxidants':"blue berries,stawberries,pomegranates,kiwis,citrus fruit,leaf greens vegetables,"

        },
        'protein': {'According to ':'World Health Organization (WHO), Dietary Guidelines for Americans, and sports nutrition research.',
            'Protein Intake (grams)': ' Body Weight (kg) × Protein Requirement (g/kg)',
                     'Based on Goals and Activity':'Optimal Protein Intake Ranges ',
                    'Sendentary(minial activity)':'0.8-1.0g/kg',
                    'moderate activity(3-5days/week)':'1.2–1.6 g/kg',
                    'High Activity':'1.6–2.2 g/kg',
                    'Weight loss':'1.6-2.4g/kg',
                    'Weight Gain/Muscle Gain':'1.6–2.2 g/kg',
                    ' Weight Gain example':'Protein = 70 × 1.8 = 126 g per day',
                    'Weight loss example':'Protein = 70 × 2.0 = 140 g per day',
                    'Weight Maintenance example':'Protein = 70 × 1.4 = 98 g per day'
                    }
    }
    
}
@app.route("/dietplan", methods=['GET', 'POST'])
def dietplan():
    if request.method == 'POST':
        # Get user input from form
        goal = request.form['goal']
        
        # Generate personalized diet plan based on goal
        plan = diet_plans.get(goal, None)
        
        if plan:
            return render_template('diet_plan.html', goal=goal, plan=plan)
        else:
            return "Invalid selection"
    return render_template('dietplan.html')

@app.route('/diet_list')
def diet_list():
    return render_template('diet_list.html')


if __name__ == '__main__':
    app.run(debug=True)
