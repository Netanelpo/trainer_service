import functions_framework
from flask import make_response

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

    # ---- Read input ----
    request_json = request.get_json(silent=True)

    if request_json and 'text' in request_json:
        text = request_json['text']
    else:
        return make_response(
            ('Missing "text" field', 400, response_headers)
        )

    # ---- Logic ----
    result = f"Hello {text}!"

    return make_response(result, 200, response_headers)
