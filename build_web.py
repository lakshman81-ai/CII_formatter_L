import os
import zipfile

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            # We don't need to zip __pycache__ or testing files
            if "__pycache__" not in root and file.endswith(".py"):
                file_path = os.path.join(root, file)
                # Keep the folder structure inside zip as "src/cii_roundtrip/..."
                arcname = os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__)))
                ziph.write(file_path, arcname)

if __name__ == '__main__':
    print("Building cii_source.zip for PyScript web interface...")
    with zipfile.ZipFile('cii_source.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir('src', zipf)
    print("Done! cii_source.zip created.")
