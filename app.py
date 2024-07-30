from datetime import datetime
import os
import time

from flask import Flask, render_template, flash, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

from flask_stuff.img_processing import convertJpgToBmp
from sqliteUtils import setup_sqlite, insert_to_db, hash_exists, get_unprinted_hashes, is_printed, \
    count_unprinted_before_hash, count_unprinted_rows, mark_as_printed, get_next_unprinted_hash, get_timestamp
from flask_stuff.utils import getFilenameWithoutExtension, allowed_file, hashFileName, getFileExtension
import threading
from escpos.printer import Serial

USE_PRINTER = False

thread_event = threading.Event()

setup_sqlite()

UPLOAD_FOLDER = './static/uploads'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def readyToRip(p):
    for i in range(4):
        p.textln('')
    app.logger.info('Ready to Rip')

def printToPrinter(filehash):
    dt = datetime.strptime(get_timestamp(filehash), '%Y-%m-%d %H:%M:%S')
    p = Serial(devfile='/dev/ttyS0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1.00, dsrdtr=True)
    p.image('./static/converted/' + filehash + '.bmp')
    p.textln('')
    p.text(dt)
    readyToRip(p)
    p.close()

def printImg(filehash):
    app.logger.info(filehash)
    if USE_PRINTER:
        printToPrinter(filehash)
    time.sleep(3)
    app.logger.info('printed')
    mark_as_printed(filehash)

def checkPrintables():
    while thread_event.is_set():
        app.logger.info('Background task running!')
        nextHash = get_next_unprinted_hash()
        if nextHash is None:
            app.logger.info('Background task done!')
            thread_event.clear()
        else:
            printImg(nextHash)
        time.sleep(1)

@app.route('/')
def index():
    hashes = get_unprinted_hashes()
    total = count_unprinted_rows()
    return render_template('index.html', hashes=hashes, total=total)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename_hash_with_ext = hashFileName(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_hash_with_ext))
            convertJpgToBmp(filename_hash_with_ext)
            return jsonify({'redirect': url_for('success', filename=filename, filehash=filename_hash_with_ext)})
    return render_template('upload.html')


@app.route('/success')
def success():
    filename = request.args.get('filename')
    filehash = request.args.get('filehash')
    return render_template("success.html",
                           filename=filename,
                           filehash=getFilenameWithoutExtension(filehash),
                           extension=getFileExtension(filehash),
                           timestamp=time.ctime()
                           )


@app.route('/print')
def print():
    filehash = request.args.get('filehash')
    if (filehash == None or filehash == ""):
        return redirect(url_for('upload'))
    path = './static/converted/' + filehash
    # send to print queue
    if (hash_exists(filehash) == False):
        insert_to_db(filehash)
        try:
            thread_event.set()

            thread = threading.Thread(target=checkPrintables)
            thread.start()
        except Exception as error:
            return str(error)
    if (is_printed(filehash) == True):
        return render_template('print.html',
                               queuePlace=0,
                               filehash=filehash
                               )
    # get place in queue
    queuePlace = str(count_unprinted_before_hash(filehash) + 1)
    if queuePlace == "1":
        queuePlace = "next"
    return render_template('print.html',
                           queuePlace=queuePlace,
                           filehash=filehash
                           )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
