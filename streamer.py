
import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server

PAGE="""\
<!DOCTYPE html>
<html>
<head>
    <title>Robot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body, html {
            width: 100%;
            height: 100%;
            overflow: hidden;
        }
        .imgbox {
            height: 87vh;
            width: 100vw;
        }
        .center-fit {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .button-container {
            display: flex;
            justify-content: space-between;
            align-items: stretch;
            height: 13vh;
            width: 100%;
            gap: 10px;
            padding: 5px;
        }
        button {
            width: calc(50% - 10px);
            height: 100%;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border: none;
            outline: none;
        }
        #counter {
            position: absolute;
            top: 10px;
            left: 10px;
            font-size: 40px; /* Increased font size for larger counter */
            color: white;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 5px;
            border-radius: 5px;
        }
        #countdown {
            font-size: 40px; /* Increased font size for larger countdown */
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            background-color: rgba(0, 0, 0, 0.7);
            padding: 10px;
            border-radius: 10px;
        }
        #goButton {
            background-color: #23db23; /* Green color for START button */
        }
        #stopButton {
            background-color: #e01b25; /* Red color for END button */
        }
    </style>
</head>
<body>
    <div class="imgbox">
        <img src="black_screen.jpg" id="streamImage" class="center-fit">
        <div id="countdown"></div>
    </div>
    <div id="counter">#0</div> <!-- Counter element with hashtag -->
    <div class="button-container">
        <button id="stopButton">END</button>
        <button id="goButton">START</button>
    </div>

    <script>
        var timer;
        var countdown;
        var countdownDisplay = document.getElementById('countdown');
        var isTimerRunning = false;
        var counter = 0; // Initialize the counter to 0

        function updateCountdownDisplay(seconds) {
            var minutes = Math.floor(seconds / 60);
            var remainingSeconds = seconds % 60;
            countdownDisplay.textContent = minutes + ':' + (remainingSeconds < 10 ? '0' : '') + remainingSeconds;
        }

        function updateCounterDisplay() {
            document.getElementById('counter').textContent = '#' + counter; // Add hashtag before the counter
        }

        document.getElementById('goButton').addEventList

"""





class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == '/black_screen.jpg':
            
            f = open('/home/linal/start.png', 'rb')
            self.send_response(200)
            self.send_header('Content-type',        'image/png')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
        elif self.path == '/game_over.jpg':
            print("this is game over")
            f = open('/home/linal/game_over.png', 'rb')
            self.send_response(200)
            self.send_header('Content-type',        'image/png')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
        
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='1280x720', framerate=24) as camera:
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
