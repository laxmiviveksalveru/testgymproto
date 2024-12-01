

```markdown
# Gym Equipment Classification Project

This project involves creating an application to classify gym equipment using machine learning models. It integrates Firebase Authentication for secure login and uses Flask for the backend. The project aims to help users identify gym machines and access tutorials based on the type of equipment.

## Features

- **Authentication**: Firebase email/password and Google authentication.
- **Gym Equipment Classification**: Classify gym equipment using trained models.
- **Trainer Profiles**: Admin can upload trainer profiles for users to view.

## Setup Instructions

### Prerequisites

Before setting up this project, ensure that you have the following installed:

- Python 3.x
- Node.js and npm
- Flask
- Firebase (for authentication)
- PostgreSQL (for database)

### Clone the repository

```bash
git clone https://github.com/your-repo/gym-equipment-classification.git
cd gym-equipment-classification
```

### Setup the Backend

1. Create a **virtual environment** for Python:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

2. Install dependencies from `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up Firebase authentication by creating a `config.py` file and adding your Firebase configuration:

   ```python
   # config.py
   firebase_config = {
       "apiKey": "<YOUR_FIREBASE_API_KEY>",
       "authDomain": "<YOUR_FIREBASE_AUTH_DOMAIN>",
       "projectId": "<YOUR_FIREBASE_PROJECT_ID>",
       "storageBucket": "<YOUR_FIREBASE_STORAGE_BUCKET>",
       "messagingSenderId": "<YOUR_FIREBASE_MESSAGING_SENDER_ID>",
       "appId": "<YOUR_FIREBASE_APP_ID>",
       "measurementId": "<YOUR_FIREBASE_MEASUREMENT_ID>"
   }
   ```

### Frontend Setup

1. Navigate to the frontend folder:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Add your Firebase configuration in `config.js` and `config1.js` as shown below:

#### `config.js`

```javascript
export const firebaseConfig = {
    apiKey: "<YOUR_FIREBASE_API_KEY>",
    authDomain: "<YOUR_FIREBASE_AUTH_DOMAIN>",
    projectId: "<YOUR_FIREBASE_PROJECT_ID>",
    storageBucket: "<YOUR_FIREBASE_STORAGE_BUCKET>",
    messagingSenderId: "<YOUR_FIREBASE_MESSAGING_SENDER_ID>",
    appId: "<YOUR_FIREBASE_APP_ID>",
    measurementId: "<YOUR_FIREBASE_MEASUREMENT_ID>"
};
```

#### `config1.js`

```javascript
export const firebaseConfig = {
    apiKey: "<YOUR_FIREBASE_API_KEY>",
    authDomain: "<YOUR_FIREBASE_AUTH_DOMAIN>",
    projectId: "<YOUR_FIREBASE_PROJECT_ID>",
    storageBucket: "<YOUR_FIREBASE_STORAGE_BUCKET>",
    messagingSenderId: "<YOUR_FIREBASE_MESSAGING_SENDER_ID>",
    appId: "<YOUR_FIREBASE_APP_ID>",
    measurementId: "<YOUR_FIREBASE_MEASUREMENT_ID>"
};
```

### Running the Application

To run the Flask app:

```bash
python app.py
```

To start the frontend, use:

```bash
npm start
```

### Important Notes

- Ensure that Firebase authentication is correctly set up before running the app.
- The database is hosted on PostgreSQL; make sure the connection details are configured correctly.
- Replace sensitive information with the appropriate environment variables.

## .gitignore

To ensure sensitive files are not exposed, the following files and directories are ignored in the `.gitignore` file:

- Firebase Configuration Files:
  - `firebase-auth.json`
  - `firebase-database.json`
  - `firebase-accessories.json`
  - `firebase_config.py`
  - `config.js`
  - `config1.js`

- Python and Node.js related files:
  - `*.env`
  - `__pycache__/`
  - `node_modules/`

- IDE/Editor files:
  - `.vscode/`
  - `.idea/`
  - `*.swp`

- Log files:
  - `*.log`

- System files:
  - `.DS_Store`
  - `Thumbs.db`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

### Changes Made:
- The sensitive details like `SECRET_KEY`, `CLOUDINARY_CLOUD_NAME`, and Firebase keys have been replaced with `<YOUR_<SERVICE>_KEY>` placeholders to ensure security.
- The section related to `.env` was updated to mention where sensitive values should be defined or replaced.

Make sure to create your `.env` file or set these variables properly in your environment when running the project.# testgymproto
