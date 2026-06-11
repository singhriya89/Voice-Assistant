import re
import datetime
import random
import requests
import wikipedia
import os
from flask import Flask, request, jsonify, send_file

# Initialize Flask App
app = Flask(__name__)

class NLPBackend:
    def __init__(self):
        # Basic NLP Stopwords to filter out conversational filler
        self.stopwords = {
            'is', 'a', 'the', 'an', 'please', 'can', 'you', 'me', 'tell', 
            'what', 'who', 'show', 'give', 'get', 'look', 'up', 'for', 'search',
            'do', 'does', 'did', 'about', 'on', 'in', 'of', 'and', 'to', 'it'
        }

    def clean_text(self, text):
        """Tokenizes text and removes stopwords."""
        words = re.findall(r"\w+", text.lower())
        return [w for w in words if w not in self.stopwords]

    def safe_eval(self, expr):
        """Safely evaluates mathematical expressions."""
        expr = expr.replace('x', '*').replace('X', '*')
        clean_expr = re.sub(r'[^0-9\.\+\-\*\/\%\(\) ]', '', expr)
        try:
            return eval(clean_expr, {'__builtins__': None}, {})
        except Exception:
            return None

    def web_search(self, query):
        """Uses DuckDuckGo API for web queries as a fallback."""
        try:
            params = {'q': query, 'format': 'json', 'no_html': 1, 'skip_disambig': 1}
            resp = requests.get('https://api.duckduckgo.com/', params=params, timeout=5)
            data = resp.json()
            abstract = data.get('AbstractText', '').strip()
            if abstract:
                return abstract
            return "I searched the web but couldn't find a concise answer for that."
        except Exception:
            return "My web search module is currently facing network issues."

    def process_query(self, raw_text):
        """Main NLP pipeline to classify intent and return a response."""
        text = raw_text.lower()
        keywords = self.clean_text(raw_text)
        print(f"[Backend Debug] Extracted Keywords: {keywords}")

        # Intent: Local UI Commands (Dark/Light Mode)
        if 'dark' in keywords and 'mode' in keywords:
            return {"response": "Dark mode is now enabled! 🌙", "command": "DARK_MODE"}
        elif 'light' in keywords and 'mode' in keywords:
            return {"response": "Light mode is now enabled! ☀️", "command": "LIGHT_MODE"}

        # Intent: Greetings
        elif any(word in keywords for word in ['hello', 'hi', 'hey', 'greetings']):
            return {"response": "Hello! I am your Python-powered NLP assistant. How can I help you?", "command": None}

        # Intent: Time
        elif 'time' in keywords:
            current_time = datetime.datetime.now().strftime('%I:%M %p')
            return {"response": f"The current time is {current_time}.", "command": None}

        # Intent: Date
        elif 'date' in keywords or 'today' in keywords:
            current_date = datetime.datetime.now().strftime('%B %d, %Y')
            return {"response": f"Today's date is {current_date}.", "command": None}

        # Intent: Jokes
        elif 'joke' in keywords or 'funny' in keywords:
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "There are 10 types of people in the world: those who understand binary, and those who don't."
            ]
            return {"response": random.choice(jokes), "command": None}

        # Intent: Math Evaluation
        elif 'calculate' in keywords or re.search(r'\d+\s*[\+\-\*\/]\s*\d+', text):
            expr = text.replace('calculate', '').replace('what is', '').strip()
            result = self.safe_eval(expr)
            if result is not None:
                return {"response": f"The answer to {expr} is <b>{result}</b>.", "command": None}

        # Intent: Wikipedia Knowledge
        elif 'wikipedia' in keywords:
            query = " ".join([w for w in keywords if w != 'wikipedia'])
            if not query:
                return {"response": "What would you like me to search on Wikipedia?", "command": None}
            try:
                result = wikipedia.summary(query, sentences=2)
                return {"response": f"<b>Wikipedia:</b><br>{result}", "command": None}
            except wikipedia.exceptions.DisambiguationError:
                return {"response": "There are multiple matches for this topic. Please be more specific.", "command": None}
            except Exception:
                return {"response": "I couldn't find a Wikipedia article matching that.", "command": None}

        # Fallback Intent: Web Search
        else:
            search_result = self.web_search(raw_text)
            return {"response": search_result, "command": None}

nlp_engine = NLPBackend()

@app.route('/')
def home():
    """
    Serves the frontend GUI. 
    By using send_file instead of render_template, we completely avoid 
    the Jinja2 TemplateNotFound error!
    """
    current_directory = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_directory, 'index.html')
    
    if not os.path.exists(html_path):
        return "Error: Please make sure your 'index.html' file is in the exact same folder as this Python file!", 404
        
    return send_file(html_path)

@app.route('/api/chat', methods=['POST'])
def chat():
    """API Endpoint that receives text from frontend and returns Python's response."""
    data = request.get_json()
    user_text = data.get('message', '')
    
    if not user_text:
        return jsonify({"response": "Please provide an input.", "command": None})
    
    # Process text through our Python NLP class
    result = nlp_engine.process_query(user_text)
    return jsonify(result)

if __name__ == '__main__':
    print("="*50)
    print("Starting Python NLP Backend on http://127.0.0.1:5000")
    print("Make sure 'index.html' is in the SAME folder as this file!")
    print("="*50)
    app.run(debug=True, port=5000)