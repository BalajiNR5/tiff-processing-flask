# routes.py
from flask import request, jsonify, send_file
from processing import process_tiff_background, progress_dict, heatmap_dict
import uuid
import os
import threading

TEMP_DIR = "tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

def init_routes(app):
    @app.route("/process", methods=["POST"])
    def process_tiff():
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        job_id = str(uuid.uuid4())
        temp_path = os.path.join(TEMP_DIR, f"{job_id}.tiff")
        file.save(temp_path)

        thread = threading.Thread(target=process_tiff_background, args=(temp_path, job_id))
        thread.start()

        return jsonify({"job_id": job_id, "status": "processing_started"})

    @app.route("/status/<job_id>", methods=["GET"])
    def check_status(job_id):
        progress = progress_dict.get(job_id, 0)
        status = "completed" if progress == 100 else ("error" if progress == -1 else "processing")
        return jsonify({"job_id": job_id, "status": status, "progress": progress})

    @app.route("/heatmap/<job_id>", methods=["GET"])
    def get_heatmap(job_id):
        heatmap_path = heatmap_dict.get(job_id)
        print(f"DEBUG: job_id={job_id}, heatmap_path={heatmap_path}")
        if not heatmap_path or not os.path.exists(heatmap_path):
            return jsonify({"error": "Heatmap not ready or invalid job_id"}), 404

        return send_file(heatmap_path, mimetype='image/png', as_attachment=True)
