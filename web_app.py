from flask import Flask, request, render_template, send_file, redirect, url_for, jsonify
import os
import tempfile
import uuid
import logging
import subprocess
import hashlib
import time
import threading
from functools import lru_cache
from werkzeug.middleware.proxy_fix import ProxyFix
from step_parser import StepParser
from comparison_engine import ComparisonEngine
from report_generator import ReportGenerator

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# Create a temporary directory for uploads and reports
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'step_comparison')
CACHE_FOLDER = os.path.join(UPLOAD_FOLDER, 'cache')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(CACHE_FOLDER):
    os.makedirs(CACHE_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CACHE_FOLDER'] = CACHE_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB max upload size

# Dictionary to store file paths for visualization
file_storage = {}
# Dictionary to store comparison results cache
comparison_cache = {}
# Dictionary to store background processing tasks
background_tasks = {}

# Calculate file hash for caching
def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file for caching purposes"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

# Cache decorator for expensive operations
@lru_cache(maxsize=32)
def get_cached_stl(file_hash):
    """Get cached STL file path if it exists"""
    cache_path = os.path.join(app.config['CACHE_FOLDER'], f"{file_hash}.stl")
    if os.path.exists(cache_path):
        logger.info(f"STL cache hit for {file_hash}")
        return cache_path
    return None

# Background processing function
def process_files_in_background(file1_path, file2_path, file1_id, file2_id, task_id):
    """Process files in background thread"""
    try:
        logger.info(f"Background task {task_id} started")
        background_tasks[task_id]['status'] = 'processing'
        
        # Calculate file hashes for caching
        file1_hash = calculate_file_hash(file1_path)
        file2_hash = calculate_file_hash(file2_path)
        
        # Check STL cache
        cached_stl1 = get_cached_stl(file1_hash)
        cached_stl2 = get_cached_stl(file2_hash)
        
        # Convert STEP files to STL for visualization
        if cached_stl1:
            # Use cached STL
            file_storage[file1_id]['stl'] = cached_stl1
        else:
            # Convert and cache
            stl_path = file_storage[file1_id]['stl']
            if not convert_step_to_stl(file1_path, stl_path):
                convert_step_to_stl(file1_path, stl_path)
            # Cache the result
            cache_path = os.path.join(app.config['CACHE_FOLDER'], f"{file1_hash}.stl")
            if os.path.exists(stl_path):
                with open(stl_path, 'rb') as src, open(cache_path, 'wb') as dst:
                    dst.write(src.read())
        
        if cached_stl2:
            # Use cached STL
            file_storage[file2_id]['stl'] = cached_stl2
        else:
            # Convert and cache
            stl_path = file_storage[file2_id]['stl']
            if not convert_step_to_stl(file2_path, stl_path):
                convert_step_to_stl(file2_path, stl_path)
            # Cache the result
            cache_path = os.path.join(app.config['CACHE_FOLDER'], f"{file2_hash}.stl")
            if os.path.exists(stl_path):
                with open(stl_path, 'rb') as src, open(cache_path, 'wb') as dst:
                    dst.write(src.read())
        
        # Check comparison cache
        cache_key = f"{file1_hash}_{file2_hash}"
        if cache_key in comparison_cache:
            logger.info(f"Using cached comparison for {cache_key}")
            background_tasks[task_id]['result'] = comparison_cache[cache_key]
        else:
            # Parse STEP files
            logger.info("Parsing file 1")
            parser = StepParser()
            data1 = parser.parse(file1_path)
            
            logger.info("Parsing file 2")
            parser = StepParser()
            data2 = parser.parse(file2_path)
            
            # Compare the files
            logger.info("Comparing files")
            engine = ComparisonEngine()
            differences = engine.compare(data1, data2, file1_path, file2_path)
            
            # Generate reports
            logger.info("Generating report")
            file1_name = os.path.basename(file1_path)
            file2_name = os.path.basename(file2_path)
            generator = ReportGenerator(differences, file1_name, file2_name)
            
            # Generate HTML report
            report_html = generator.generate_html_report()
            
            # Generate PDF report
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"report_{task_id}.pdf")
            generator.generate_pdf_report(pdf_path)
            
            # Generate CSV report
            csv_path = os.path.join(app.config['UPLOAD_FOLDER'], f"report_{task_id}.csv")
            generator.generate_csv_report(csv_path)
            
            # Store result
            result = {
                'differences': differences,
                'report_html': report_html,
                'pdf_path': pdf_path,
                'csv_path': csv_path
            }
            
            # Cache the result
            comparison_cache[cache_key] = result
            background_tasks[task_id]['result'] = result
        
        background_tasks[task_id]['status'] = 'completed'
        logger.info(f"Background task {task_id} completed")
    except Exception as e:
        logger.error(f"Error in background task {task_id}: {str(e)}")
        background_tasks[task_id]['status'] = 'error'
        background_tasks[task_id]['error'] = str(e)

@app.route('/')
def index():
    return render_template('index.html')

def convert_step_to_stl(step_file, stl_file):
    """Convert STEP file to STL using OCC"""
    try:
        logger.info(f"Starting STEP to STL conversion: {step_file} -> {stl_file}")
        
        # Check if input file exists and has content
        if not os.path.exists(step_file):
            logger.error(f"STEP file does not exist: {step_file}")
            return False
            
        file_size = os.path.getsize(step_file)
        logger.info(f"STEP file size: {file_size} bytes")
        
        if file_size == 0:
            logger.error(f"STEP file is empty: {step_file}")
            return False
        
        # Import OCC modules
        try:
            from OCC.Core.STEPControl import STEPControl_Reader
            from OCC.Core.IFSelect import IFSelect_RetDone
            from OCC.Core.StlAPI import StlAPI_Writer
            from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
            logger.info("Successfully imported OCC modules")
        except ImportError as e:
            logger.error(f"Failed to import OCC modules: {str(e)}")
            return False
        
        # Read STEP file
        logger.info("Creating STEP reader")
        step_reader = STEPControl_Reader()
        logger.info(f"Reading STEP file: {step_file}")
        status = step_reader.ReadFile(step_file)
        logger.info(f"Read status: {status}")
        
        if status == IFSelect_RetDone:
            logger.info("Transferring roots")
            step_reader.TransferRoots()
            logger.info("Getting shape")
            shape = step_reader.OneShape()
            
            # Mesh the shape
            logger.info("Meshing shape")
            mesh = BRepMesh_IncrementalMesh(shape, 0.1)
            mesh.Perform()
            
            # Write STL file
            logger.info(f"Writing STL file: {stl_file}")
            stl_writer = StlAPI_Writer()
            result = stl_writer.Write(shape, stl_file)
            logger.info(f"Write result: {result}")
            
            # Check if STL file was created
            if os.path.exists(stl_file):
                stl_size = os.path.getsize(stl_file)
                logger.info(f"STL file created, size: {stl_size} bytes")
                if stl_size < 100:
                    logger.warning(f"STL file is suspiciously small: {stl_size} bytes")
            else:
                logger.error(f"STL file was not created: {stl_file}")
                return False
            
            logger.info(f"Successfully converted {step_file} to {stl_file}")
            return True
        else:
            logger.error(f"Failed to read STEP file: {step_file}")
            return False
    except Exception as e:
        logger.error(f"Error converting STEP to STL: {str(e)}")
        return False

def create_fallback_stl(stl_file):
    """Create a simple cube STL as a fallback"""
    try:
        logger.info(f"Creating fallback STL cube: {stl_file}")
        # Simple STL file for a cube
        with open(stl_file, 'w') as f:
            f.write("""solid cube
facet normal 0 0 1
    outer loop
        vertex 0 0 0
        vertex 1 0 0
        vertex 1 1 0
    endloop
endfacet
facet normal 0 0 1
    outer loop
        vertex 0 0 0
        vertex 1 1 0
        vertex 0 1 0
    endloop
endfacet
facet normal 0 0 -1
    outer loop
        vertex 0 0 1
        vertex 1 1 1
        vertex 1 0 1
    endloop
endfacet
facet normal 0 0 -1
    outer loop
        vertex 0 0 1
        vertex 0 1 1
        vertex 1 1 1
    endloop
endfacet
facet normal 0 1 0
    outer loop
        vertex 0 1 0
        vertex 1 1 0
        vertex 1 1 1
    endloop
endfacet
facet normal 0 1 0
    outer loop
        vertex 0 1 0
        vertex 1 1 1
        vertex 0 1 1
    endloop
endfacet
facet normal 0 -1 0
    outer loop
        vertex 0 0 0
        vertex 1 0 1
        vertex 1 0 0
    endloop
endfacet
facet normal 0 -1 0
    outer loop
        vertex 0 0 0
        vertex 0 0 1
        vertex 1 0 1
    endloop
endfacet
facet normal 1 0 0
    outer loop
        vertex 1 0 0
        vertex 1 0 1
        vertex 1 1 1
    endloop
endfacet
facet normal 1 0 0
    outer loop
        vertex 1 0 0
        vertex 1 1 1
        vertex 1 1 0
    endloop
endfacet
facet normal -1 0 0
    outer loop
        vertex 0 0 0
        vertex 0 1 1
        vertex 0 0 1
    endloop
endfacet
facet normal -1 0 0
    outer loop
        vertex 0 0 0
        vertex 0 1 0
        vertex 0 1 1
    endloop
endfacet
endsolid cube""")
        return True
    except Exception as e:
        logger.error(f"Error creating fallback STL: {str(e)}")
        return False

def convert_step_to_stl_using_occ(step_file, stl_file):
    """Convert STEP to STL using OpenCascade directly"""
    try:
        logger.info(f"Converting {step_file} to {stl_file} using OCC")
        
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.StlAPI import StlAPI_Writer
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
        from OCC.Core.IFSelect import IFSelect_RetDone
        
        # Read the STEP file
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(step_file)
        
        if status == IFSelect_RetDone:
            step_reader.TransferRoots()
            shape = step_reader.Shape()
            
            # Mesh the shape
            mesh = BRepMesh_IncrementalMesh(shape, 0.1)
            mesh.Perform()
            
            # Write to STL
            stl_writer = StlAPI_Writer()
            stl_writer.Write(shape, stl_file)
            
            logger.info(f"Successfully converted {step_file} to {stl_file}")
            return True
        else:
            logger.error(f"Failed to read STEP file: {step_file}")
            return False
    except Exception as e:
        logger.error(f"Error in OCC conversion: {str(e)}")
        return False

@app.route('/compare', methods=['POST'])
def compare():
    try:
        # Check if files were uploaded
        if 'file1' not in request.files or 'file2' not in request.files:
            return "No files uploaded", 400
        
        file1 = request.files['file1']
        file2 = request.files['file2']
        
        # Check if files have names
        if file1.filename == '' or file2.filename == '':
            return "No files selected", 400
        
        # Generate unique IDs for the files
        file1_id = str(uuid.uuid4())
        file2_id = str(uuid.uuid4())
        
        # Save the uploaded files
        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file1_id}_{file1.filename}")
        file2_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file2_id}_{file2.filename}")
        
        file1.save(file1_path)
        file2.save(file2_path)
        
        # Store file paths for later use
        file_storage[file1_id] = {
            'path': file1_path,
            'stl': os.path.join(app.config['UPLOAD_FOLDER'], f"{file1_id}.stl")
        }
        
        file_storage[file2_id] = {
            'path': file2_path,
            'stl': os.path.join(app.config['UPLOAD_FOLDER'], f"{file2_id}.stl")
        }
        
        # Create a task ID for background processing
        task_id = str(uuid.uuid4())
        background_tasks[task_id] = {
            'status': 'queued',
            'file1_id': file1_id,
            'file2_id': file2_id,
            'file1_name': file1.filename,
            'file2_name': file2.filename,
            'created_at': time.time()
        }
        
        # Start background processing
        thread = threading.Thread(
            target=process_files_in_background,
            args=(file1_path, file2_path, file1_id, file2_id, task_id)
        )
        thread.daemon = True
        thread.start()
        
        # Redirect to the processing page
        return redirect(url_for('processing', task_id=task_id))
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/processing/<task_id>')
def processing(task_id):
    if task_id not in background_tasks:
        return "Task not found", 404
    
    task = background_tasks[task_id]
    return render_template('processing.html', 
                          task_id=task_id, 
                          file1_name=task['file1_name'],
                          file2_name=task['file2_name'])

@app.route('/api/task_status/<task_id>')
def task_status(task_id):
    if task_id not in background_tasks:
        return jsonify({'status': 'not_found'}), 404
    
    task = background_tasks[task_id]
    response = {
        'status': task['status'],
        'file1_name': task['file1_name'],
        'file2_name': task['file2_name']
    }
    
    if task['status'] == 'error' and 'error' in task:
        response['error'] = task['error']
    
    if task['status'] == 'completed':
        response['redirect'] = url_for('show_results', task_id=task_id)
    
    return jsonify(response)

@app.route('/results/<task_id>')
def show_results(task_id):
    if task_id not in background_tasks:
        return "Task not found", 404
    
    task = background_tasks[task_id]
    
    if task['status'] != 'completed':
        return redirect(url_for('processing', task_id=task_id))
    
    result = task.get('result', {})
    
    return render_template('compare_result.html', 
                          file1_id=task['file1_id'],
                          file2_id=task['file2_id'],
                          file1_name=task['file1_name'],
                          file2_name=task['file2_name'],
                          comparison_results=result.get('report_html', ''),
                          task_id=task_id)

@app.route('/export/pdf/<task_id>')
def export_pdf(task_id):
    if task_id not in background_tasks or background_tasks[task_id]['status'] != 'completed':
        return "Report not available", 404
    
    result = background_tasks[task_id].get('result', {})
    pdf_path = result.get('pdf_path')
    
    if not pdf_path or not os.path.exists(pdf_path):
        return "PDF report not available", 404
    
    return send_file(pdf_path, 
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"comparison_report_{task_id}.pdf")

@app.route('/export/csv/<task_id>')
def export_csv(task_id):
    if task_id not in background_tasks or background_tasks[task_id]['status'] != 'completed':
        return "Report not available", 404
    
    result = background_tasks[task_id].get('result', {})
    csv_path = result.get('csv_path')
    
    if not csv_path or not os.path.exists(csv_path):
        return "CSV report not available", 404
    
    return send_file(csv_path, 
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f"comparison_report_{task_id}.csv")

@app.route('/api/check_stl/<file_id>')
def check_stl(file_id):
    """Check if STL file exists and is valid"""
    if file_id not in file_storage:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404
    
    stl_path = file_storage[file_id].get('stl')
    if not stl_path or not os.path.exists(stl_path):
        return jsonify({'status': 'error', 'message': 'STL file not found'}), 404
    
    # Check if file is not empty
    if os.path.getsize(stl_path) < 100:  # Minimum size for a valid STL
        return jsonify({'status': 'error', 'message': 'STL file is invalid or empty'}), 400
    
    return jsonify({'status': 'success', 'path': stl_path})

@app.route('/get_stl/<file_id>')
def get_stl(file_id):
    """Serve STL file for visualization"""
    if file_id not in file_storage:
        logger.error(f"File ID {file_id} not found in storage")
        return "File not found", 404
    
    stl_path = file_storage[file_id].get('stl')
    if not stl_path or not os.path.exists(stl_path):
        logger.error(f"STL file not found at path: {stl_path}")
        return "STL file not found", 404
    
    # Log file size and check if it's valid
    file_size = os.path.getsize(stl_path)
    logger.info(f"Serving STL file: {stl_path}, size: {file_size} bytes")
    
    # Check if file is not empty
    if file_size < 100:  # Minimum size for a valid STL
        logger.error(f"STL file is too small (possibly invalid): {file_size} bytes")
        return "Invalid STL file", 400
    
    # Try to read the first few bytes to check if it's a valid STL
    try:
        with open(stl_path, 'rb') as f:
            header = f.read(80)
            logger.info(f"STL header starts with: {header[:20]}")
    except Exception as e:
        logger.error(f"Error reading STL file: {str(e)}")
    
    return send_file(stl_path, mimetype='application/octet-stream')

# Cleanup function to remove temporary files
@app.teardown_appcontext
def cleanup_files(exception):
    for file_id, paths in list(file_storage.items()):
        try:
            # Remove files older than 1 hour (implement this with file timestamps)
            # For now, we'll keep files for the session
            pass
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True) 