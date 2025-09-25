from flask import Flask, jsonify, request, Response, stream_with_context
from llm_tools import analyze_comp
from datetime import datetime
import time, json

app = Flask(__name__)


@app.route('/api/generate', methods=['POST'])
def generate_text():
    data = request.get_json()
    prompt = data.get("prompt", "")
    model = data.get("model", "")
    stream = data.get("stream", False)

    def generate_stream():
        """ Generator function to stream response chunks. """
        for chunk in analyze_comp(prompt):
            response_data = {
                "model": model,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "response": chunk,
                "done": False
            }
            yield json.dumps(response_data) + "\n"

        # Send final completion message
        final_response = {
            "model": model,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "response": "[STREAMING COMPLETED]",
            "done": True,
        }
        yield json.dumps(final_response) + "\n"

    if stream:
        return Response(stream_with_context(generate_stream()), content_type='application/json')
    else:
        start_time = time.perf_counter()
        res = "\n".join(analyze_comp(prompt))
        end_time = time.perf_counter()

        response_data = {
            "model": model,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "response": res,
            "done": True,
            "context": [1, 2, 3],
            "total_duration": end_time - start_time,
            "load_duration": end_time - start_time,
            "prompt_eval_count": -1,
            "prompt_eval_duration": -1,
            "eval_count": -1,
            "eval_duration": -1
        }

        return jsonify(response_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
