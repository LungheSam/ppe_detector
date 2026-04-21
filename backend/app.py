from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
PHOTO_BASE_PATH = '/home/naruto/Documents/Programming/Others/PPE_Detector/ppe_detector/computer_vision/logs'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def get_photo_files():
    """Get all photo files with their metadata"""
    photos = []
    
    if not os.path.exists(PHOTO_BASE_PATH):
        return photos
    
    for filename in os.listdir(PHOTO_BASE_PATH):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            file_path = os.path.join(PHOTO_BASE_PATH, filename)
            file_stat = os.stat(file_path)
            
            # Parse filename to extract metadata
            # Expected format: ppe_success_{uid}_{timestamp}.jpg
            parts = filename.replace('.jpg', '').replace('.png', '').split('_')
            
            metadata = {
                'filename': filename,
                'url': f'/api/photos/{filename}',
                'size': file_stat.st_size,
                'created_time': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                'created_date': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d'),
                'created_time_str': datetime.fromtimestamp(file_stat.st_ctime).strftime('%H:%M:%S')
            }
            
            # Try to extract UID from filename
            if len(parts) >= 3:
                metadata['card_uid'] = parts[2] if parts[2] != 'null' else 'unknown'
            else:
                metadata['card_uid'] = 'unknown'
            
            photos.append(metadata)
    
    # Sort by creation time (newest first)
    photos.sort(key=lambda x: x['created_time'], reverse=True)
    return photos

@app.route('/api/photos', methods=['GET'])
def get_photos():
    """Get list of all photos"""
    try:
        photos = get_photo_files()
        return jsonify({
            'success': True,
            'count': len(photos),
            'photos': photos
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/photos/<filename>', methods=['GET'])
def serve_photo(filename):
    """Serve a specific photo file"""
    try:
        # Security check: prevent directory traversal
        if '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        file_path = os.path.join(PHOTO_BASE_PATH, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Photo not found'}), 404
        
        return send_file(file_path, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/photos/recent/<int:limit>', methods=['GET'])
def get_recent_photos(limit):
    """Get most recent N photos"""
    try:
        photos = get_photo_files()
        recent = photos[:limit]
        return jsonify({
            'success': True,
            'count': len(recent),
            'photos': recent
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/photos/date/<date>', methods=['GET'])
def get_photos_by_date(date):
    """Get photos by specific date (YYYY-MM-DD)"""
    try:
        all_photos = get_photo_files()
        filtered = [p for p in all_photos if p['created_date'] == date]
        return jsonify({
            'success': True,
            'count': len(filtered),
            'date': date,
            'photos': filtered
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/photos/card/<uid>', methods=['GET'])
def get_photos_by_card(uid):
    """Get photos for a specific card UID"""
    try:
        all_photos = get_photo_files()
        filtered = [p for p in all_photos if p.get('card_uid') == uid]
        return jsonify({
            'success': True,
            'count': len(filtered),
            'card_uid': uid,
            'photos': filtered
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'photo_path': PHOTO_BASE_PATH,
        'photos_count': len(get_photo_files())
    })

if __name__ == '__main__':
    print(f"📸 PPE Photo Server Starting...")
    print(f"📁 Photo directory: {PHOTO_BASE_PATH}")
    print(f"🌐 Server running at: http://localhost:5000")
    print(f"📷 API endpoints:")
    print(f"   GET  /api/photos           - List all photos")
    print(f"   GET  /api/photos/<filename> - Get photo file")
    print(f"   GET  /api/photos/recent/5  - Get 5 most recent")
    print(f"   GET  /api/health           - Health check")
    app.run(host='0.0.0.0', port=5000, debug=True)