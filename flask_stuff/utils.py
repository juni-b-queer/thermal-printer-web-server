import hashlib
import os
import time

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

def hashFileName(filename):
    # Get the file extension
    filename_base, filename_ext = os.path.splitext(filename)
    # Create a hash for the filename base
    with_time = filename_base + '_' + str(time.time())
    filename_hash = hashlib.sha256(with_time.encode()).hexdigest()
    # Append the extension back onto the hashed filename base
    filename_hash_with_ext = filename_hash + filename_ext
    return filename_hash_with_ext

def getFilenameWithoutExtension(filename):
    filename_base, filename_ext = os.path.splitext(filename)
    return filename_base

def getFileExtension(filename):
    filename_base, filename_ext = os.path.splitext(filename)
    return filename_ext

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
