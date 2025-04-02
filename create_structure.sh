# Create backend directory and its subdirectories and files
mkdir backend
cd backend
mkdir app
mkdir app/routes
mkdir app/services
mkdir app/utils
touch app/__init__.py
touch app/main.py
touch app/routes/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py
touch requirements.txt
touch .env
cd ..

# Create frontend directory and its subdirectories and files
mkdir frontend
cd frontend
mkdir src
mkdir src/components
touch src/App.js
touch src/App.css
touch src/index.js
touch src/index.css
mkdir public
touch public/index.html
touch package.json
# You can add yarn.lock or package-lock.json if you have them already
# touch yarn.lock
# touch package-lock.json
cd ..

# Create the README.md file in the root directory
touch README.md

echo "Project structure created successfully!"
echo "Remember to navigate into each directory to initialize your backend and frontend projects (e.g., 'npm init -y' in frontend, 'pip init' or similar in backend)."
echo "Also, install the necessary dependencies in each directory."