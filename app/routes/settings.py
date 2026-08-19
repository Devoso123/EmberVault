from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.utils.decorators import login_required

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('/theme', methods=['GET'])
@login_required
def get_theme():
    return jsonify({'theme': g.user.theme_preference}), 200

@settings_bp.route('/theme', methods=['PUT'])
@login_required
def set_theme():
    data = request.get_json()
    theme = data.get('theme')
    if not theme:
        return jsonify({'error': 'Theme required'}), 400
    allowed_themes = ['light', 'dark', 'system', 'old-money', 'emerald', 'midnight', 'sunset', 'ocean', 'lavender', 'forest', 'coffee', 'rose', 'gold', 'silver', 'bronze', 'platinum', 'diamond', 'ruby', 'sapphire', 'emerald']
    if theme not in allowed_themes:
        return jsonify({'error': 'Invalid theme'}), 400
    g.user.theme_preference = theme
    db.session.commit()
    return jsonify({'message': 'Theme updated', 'theme': theme}), 200