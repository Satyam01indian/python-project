# app.py
from flask import Flask, request, render_template_string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3

app = Flask(__name__)

def get_documents():
    conn = sqlite3.connect('search.db')
    c = conn.cursor()
    c.execute('SELECT url, content FROM pages')
    rows = c.fetchall()
    conn.close()
    return rows

@app.route('/', methods=['GET', 'POST'])
def home():
    results = []
    if request.method == 'POST':
        query = request.form['query']
        rows = get_documents()
        urls = [row[0] for row in rows]
        contents = [row[1] for row in rows]

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(contents)
        query_vec = vectorizer.transform([query])
        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
        ranked = sorted(zip(urls, scores), key=lambda x: x[1], reverse=True)
        results = [(url, score) for url, score in ranked if score > 0]

    return render_template_string('''
        <h2>Mini Search Engine</h2>
        <form method="post">
            <input name="query" placeholder="Enter your search..." size="40">
            <input type="submit" value="Search">
        </form>
        <ul>
        {% for url, score in results %}
            <li><a href="{{ url }}">{{ url }}</a> - Score: {{ "%.2f"|format(score) }}</li>
        {% endfor %}
        </ul>
    ''', results=results)

if __name__ == '__main__':
    app.run(debug=True)