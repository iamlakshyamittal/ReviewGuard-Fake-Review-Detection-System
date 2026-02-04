"""
Flask REST API for ReviewGuard
Real-time fake review detection service
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import traceback
from src.predict import FakeReviewDetector
from src.utils import setup_logger
import config.settings as settings

API_HOST = settings.API_HOST
API_PORT = settings.API_PORT
API_DEBUG = settings.API_DEBUG

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup logger
logger = setup_logger(__name__)

# Initialize detector (loaded once at startup)
try:
    detector = FakeReviewDetector()
    logger.info("ReviewGuard API initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize detector: {e}")
    detector = None


# ================= HOME (FRONTEND) =================
@app.route('/', methods=['GET'])
def home():
    return render_template("index.html")


# ================= HEALTH CHECK =================
@app.route('/health', methods=['GET'])
def health():
    if detector is None:
        return jsonify({
            'status': 'unhealthy',
            'message': 'Model not loaded'
        }), 503

    return jsonify({
        'status': 'healthy',
        'model_loaded': True
    })


# ================= SINGLE PREDICTION =================
@app.route('/predict', methods=['POST'])
def predict():
    if detector is None:
        return jsonify({'error': 'Model not loaded'}), 503

    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        if 'review_text' not in data or 'rating' not in data:
            return jsonify({'error': 'Missing review_text or rating'}), 400

        review_text = data['review_text']
        rating = float(data['rating'])

        if not (1 <= rating <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400

        result = detector.predict(
            review_text=review_text,
            rating=rating,
            reviewer_total_reviews=data.get('reviewer_total_reviews', 1),
            reviewer_avg_rating=data.get('reviewer_avg_rating', None)
        )

        return jsonify(result)

    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500


# ================= BATCH PREDICTION =================
@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    if detector is None:
        return jsonify({'error': 'Model not loaded'}), 503

    try:
        data = request.get_json()
        reviews = data.get('reviews', [])

        results = []
        for review in reviews:
            try:
                result = detector.predict(
                    review_text=review['review_text'],
                    rating=review['rating'],
                    reviewer_total_reviews=review.get('reviewer_total_reviews', 1),
                    reviewer_avg_rating=review.get('reviewer_avg_rating', None)
                )
                results.append(result)
            except:
                results.append({'error': 'Invalid review data'})

        return jsonify({'results': results})

    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500


# ================= RUN SERVER =================
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("  ReviewGuard API Server")
    print("=" * 70)
    print(f"  Starting server on {API_HOST}:{API_PORT}")
    print(f"  Debug mode: {API_DEBUG}")
    print("=" * 70 + "\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
