import functions_framework
from flask import make_response, jsonify

@functions_framework.http
def start(request):
    # ---- CORS ----
    if request.method == 'OPTIONS':
        response = make_response('', 204)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    response_headers = {
        'Access-Control-Allow-Origin': '*'
    }

    request_json = request.get_json(silent=True)

    if not request_json or 'text' not in request_json:
        return make_response(
            jsonify({'error': 'Missing "text"'}),
            400,
            response_headers
        )

    text = request_json['text']

    return make_response(
        jsonify({'result': f'Hello {text}!'}),
        200,
        response_headers
    )
