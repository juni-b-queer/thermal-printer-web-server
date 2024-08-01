import glob
from datetime import datetime
import os
import time

from flask import Flask, render_template, flash, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

from flask_stuff.img_processing import convertJpgToBmp
from sqliteUtils import setup_sqlite, insert_to_db, hash_exists, get_unprinted_hashes, is_printed, \
    count_unprinted_before_hash, count_unprinted_rows, mark_as_printed, get_next_unprinted_hash, get_timestamp, \
    delete_row, get_printed_hashes, count_printed_rows, get_originalExt, set_printed_status, get_entry_from_db, \
    total_count_printed
from flask_stuff.utils import getFilenameWithoutExtension, allowed_file, hashFileName, getFileExtension
import threading
# import board
# import neopixel
from escpos.printer import Serial

# import RPi.GPIO as GPIO

USE_PRINTER = False
IS_PRINTING = False

print_event = threading.Event()

setup_sqlite()

UPLOAD_FOLDER = './static/uploads'
# UPLOAD_FOLDER = '/home/pi/WebServer/static/uploads'
CONVERT_FOLDER = './static/converted'
# CONVERT_FOLDER = '/home/pi/WebServer/static/converted'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# region neopixels
# GPIO.setmode(GPIO.BCM)
#
# GPIO.setup(26, GPIO.OUT)

def printerOn():
    # GPIO.output(26, GPIO.LOW)
    app.logger.info('Printer on')


def printerOff():
    # GPIO.output(26, GPIO.HIGH)
    app.logger.info('Printer off')


printerOff()

# pixels = neopixel.NeoPixel(board.D18, 13)

RED = 0xF00000
GREEN = 0x00F000
BLUE = 0x0000F0
PURPLE = 0xF000F0
WHITE = 0xA3A3A3
BRIGHT = 0xFFFFFF
DIM = 0x353535
OFF = 0x000000


def setLED(color):
    # global pixels
    # pixels[0] = color
    # pixels.show()
    return True


def flashLED(c, flashes=5):
    global OFF
    for i in range(flashes):
        setLED(OFF)
        time.sleep(0.2)
        setLED(c)
        time.sleep(0.2)


def setRing(color):
    # global pixels
    # for i in range(12):
    #     pixels[i+1] = color
    # pixels.show()
    return True


def flashRing(c, flashes=5):
    global OFF
    for i in range(flashes):
        setRing(OFF)
        time.sleep(0.2)
        setRing(c)
        time.sleep(0.2)


def lightNpixels(color, count):
    return True
    # global pixels, OFF
    # setRing(OFF)
    # if count > 12:
    #     setRing(color)
    # else:
    #     for i in range(count):
    #         pixels[i+1] = color
    #     pixels.show()


# endregion

# region printing

def readyToRip(p):
    for i in range(4):
        p.textln('')
    app.logger.info('Ready to Rip')


def printToPrinter(filehash):
    dt = datetime.strptime(get_timestamp(filehash), '%Y-%m-%d %H:%M:%S')
    p = Serial(devfile='/dev/ttyS0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1.00, dsrdtr=True)
    p.image(CONVERT_FOLDER + '/' + filehash + '.bmp')
    p.textln('')
    p.text(dt.ctime())
    readyToRip(p)
    p.close()


def printImg(filehash):
    global OFF, BLUE, relayPrinter
    app.logger.info(filehash)
    setLED(BLUE)
    if USE_PRINTER:
        printToPrinter(filehash)
    time.sleep(3)
    app.logger.info('printed')
    mark_as_printed(filehash)
    setLED(OFF)


def checkPrintables():
    global BLUE, IS_PRINTING
    IS_PRINTING = True
    printerOn()
    while print_event.is_set():
        total = count_unprinted_rows()
        lightNpixels(BLUE, total)
        time.sleep(3)
        app.logger.warning('Background task running!')
        nextHash = get_next_unprinted_hash()
        if nextHash is None:
            app.logger.warning('Background task done!')
            printerOff()
            IS_PRINTING = False
            print_event.clear()
        elif not os.path.isfile(CONVERT_FOLDER + '/' + nextHash + '.bmp'):
            hashExt = get_originalExt(nextHash)
            uploadExists = os.path.isfile(UPLOAD_FOLDER + '/' + nextHash + hashExt)
            if uploadExists:
                convertJpgToBmp(nextHash + hashExt)
            else:
                delete_row(nextHash)
        else:
            printImg(nextHash)

        time.sleep(1)


# endregion

# region fileManagement

def findOriginalFile(filehash):
    path = UPLOAD_FOLDER + '/'
    file_list = glob.glob(os.path.join(path, filehash + '.*'))
    try:
        filename_with_path = next(iter(file_list))
    except StopIteration:
        filename_with_path = None

    if filename_with_path is None:
        print('No file matched the pattern')
        return False

    return (filename_with_path.split('/')[-1]).split('\\')[-1]


# endregion

def startPrinting():
    global IS_PRINTING
    app.logger.warning('Try')
    if IS_PRINTING == False:
        app.logger.info('Try')
        try:
            print_event.set()
            thread = threading.Thread(target=checkPrintables)
            thread.start()
        except Exception as error:
            return str(error)
        return True
    return True


# region routes
@app.route('/')
def index():
    totalImagesPrinted = total_count_printed()
    queuedHashes = get_unprinted_hashes()
    printedHashes = get_printed_hashes()
    printedTotal = count_printed_rows()
    queuedTotal = count_unprinted_rows()
    return render_template('index.html', printedHashes=printedHashes, queuedHashes=queuedHashes,
                           printedTotal=printedTotal, queuedTotal=queuedTotal, totalImagesPrinted=totalImagesPrinted)


@app.route('/queue', defaults={'page': 1})
@app.route('/queue/<int:page>', methods=['GET'])
def queue(page=1):
    offset = (page - 1) * 9
    hashes = get_unprinted_hashes(offset, 9)
    total = count_unprinted_rows()
    return render_template('queue.html', hashes=hashes, total=total, page=page)


@app.route('/previous', defaults={'page': 1})
@app.route('/previous/<int:page>', methods=['GET'])
def previous(page=1):
    totalImagesPrinted = total_count_printed()
    offset = (page - 1) * 9
    hashes = get_printed_hashes(offset, 9)
    total = count_printed_rows()
    app.logger.warning(total)
    return render_template('previous.html', hashes=hashes, total=total, page=page,
                           totalImagesPrinted=totalImagesPrinted)


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
            # return redirect(url_for('success', filename=filename, filehash=filename_hash_with_ext))
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


@app.route('/cancel')
def cancel():
    filehash = request.args.get('filehash')
    set_printed_status(filehash, 1)
    return redirect(url_for('print', filehash=filehash))


@app.route('/reprint')
def reprint():
    filehash = request.args.get('filehash')
    set_printed_status(filehash, 0)
    startPrinting()
    return redirect(url_for('print', filehash=filehash))


@app.route('/print')
def print():
    global IS_PRINTING
    filehash = request.args.get('filehash')
    if (filehash == None or filehash == ""):
        return redirect(url_for('upload'))
    # send to print queue
    if not hash_exists(filehash):
        originalExt = getFileExtension(findOriginalFile(filehash))
        insert_to_db(filehash, originalExt)
        startPrinting()
    dbEntry = get_entry_from_db(filehash)
    app.logger.warning(dbEntry)
    if (is_printed(filehash) == True):
        return render_template('print.html',
                               queuePlace=0,
                               filehash=filehash,
                               countPrinted=dbEntry['count_printed'],
                               )
    # get place in queue
    queuePlace = str(count_unprinted_before_hash(filehash) + 1)
    if queuePlace == "1":
        queuePlace = "next"
    return render_template('print.html',
                           queuePlace=queuePlace,
                           filehash=filehash,
                           countPrinted=dbEntry['count_printed']
                           )


# endregion

setLED(GREEN)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='80')
