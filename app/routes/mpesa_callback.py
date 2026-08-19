from flask import Blueprint, request, jsonify
import logging

mpesa_cb_bp = Blueprint('mpesa_cb', __name__, url_prefix='/mpesa')

@mpesa_cb_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()
    logging.info(f"M-Pesa Callback received: {data}")
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'})