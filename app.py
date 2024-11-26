from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv
from google.cloud import storage
import pandas as pd
from io import BytesIO

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')    # Host MySQL
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')         # Username MySQL
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')     # Password MySQL
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'library')          # Nama database

mysql = MySQL(app)

# Endpoint untuk mendapatkan semua buku
@app.route('/api/books', methods=['GET'])
def get_books():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM books')
    books = cur.fetchall()
    cur.close()
    return jsonify(books)

# Endpoint untuk menambahkan buku baru
@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.get_json()
    
    # Validasi input
    required_fields = ['title', 'description', 'authors', 'image', 'publisher', 'publishedDate', 'categories', 'review_score']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    title = data['title']
    description = data['description']
    authors = data['authors']
    image = data['image']
    publisher = data['publisher']
    publishedDate = data['publishedDate']
    categories = data['categories']
    review_score = data['review_score']

    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO books (title, description, authors, image, publisher, publishedDate, categories, review_score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', 
                (title, description, authors, image, publisher, publishedDate, categories, review_score))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Book added successfully!'}), 201

# Endpoint untuk mengimpor data dari CSV di Google Cloud Storage
@app.route('/import_books_from_csv', methods=['POST'])
def import_books_from_csv():
    BUCKET_NAME = 'your-bucket-name'      # Ganti dengan nama bucket Anda
    CSV_FILE_NAME = 'your-file-name.csv'  # Ganti dengan nama file CSV Anda

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(CSV_FILE_NAME)

    csv_data = blob.download_as_bytes()

    df = pd.read_csv(BytesIO(csv_data))

    for index, row in df.iterrows():
        title = row['title']
        description = row['description']
        authors = row['authors']
        image = row['image']
        publisher = row['publisher']
        publishedDate = row['publishedDate']
        categories = row['categories']
        review_score = row['review_score']
        
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO books (title, description, authors, image, publisher, publishedDate, categories, review_score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', 
                    (title, description, authors, image, publisher, publishedDate, categories, review_score))
        mysql.connection.commit()
        cur.close()
    
    return jsonify({'message': f'Books imported from {CSV_FILE_NAME} successfully!'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
