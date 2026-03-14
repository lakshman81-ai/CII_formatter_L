import os
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from src.cii_roundtrip.web.config import Config
from src.cii_roundtrip.parser import Parser
from src.cii_roundtrip.export_csv import generate_custom_csv
from src.cii_roundtrip.import_csv import import_csv_to_cii
from src.cii_roundtrip.serializer import serialize_to_cii
from src.cii_roundtrip.comparator import compare_files

app = Flask(__name__)
app.config.from_object(Config)

ALLOWED_EXTENSIONS = {'cii', 'neu', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload_cii', methods=['POST'])
def upload_cii():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            p = Parser(filepath, n1_allocation=2000)
            data = p.parse()

            # Export to CSV automatically
            csv_filename = filename.rsplit('.', 1)[0] + '_exported.csv'
            csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
            generate_custom_csv(data, export_path=csv_path)

            return jsonify({
                "message": "File processed successfully",
                "cii_file": filename,
                "csv_file": csv_filename,
                "elements_count": len(data.elements)
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400

@app.route('/api/download/<filename>')
def download_file(filename):
    secure_name = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

@app.route('/api/reconstruct', methods=['POST'])
def reconstruct():
    """
    Takes the original CII file name and the updated CSV file name,
    reconstructs the CII, and returns the comparison results and the new file.
    """
    data = request.json
    orig_cii = data.get('cii_file')
    csv_file = data.get('csv_file')

    if not orig_cii or not csv_file:
        return jsonify({"error": "Missing file references"}), 400

    orig_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(orig_cii))
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(csv_file))

    if not os.path.exists(orig_path) or not os.path.exists(csv_path):
        return jsonify({"error": "Uploaded files not found on server"}), 404

    try:
        # Parse original to get base data
        p = Parser(orig_path, n1_allocation=2000)
        base_data = p.parse()

        # Import modified CSV over base data
        new_data = import_csv_to_cii(csv_path, base_cii_data=base_data)

        # Serialize new CII
        new_cii_filename = "reconstructed_" + orig_cii
        new_cii_path = os.path.join(app.config['UPLOAD_FOLDER'], new_cii_filename)
        serialize_to_cii(new_data, new_cii_path)

        # Compare
        report = compare_files(orig_path, new_cii_path)

        return jsonify({
            "message": "Reconstruction successful",
            "reconstructed_file": new_cii_filename,
            "report": report
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
