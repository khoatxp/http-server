import socket
import email.utils
import os, sys
import datetime
from threading import Thread

# Copy of the function in single thread
def handle_request(request):
    headers = request.split('\r\n')

    # Get the first header for filename information
    filename = None
    first_header_fields = headers[0].split(" ")

    if len(first_header_fields) == 3:
        if first_header_fields[2] != 'HTTP/1.1':
            return 'HTTP/1.1 400 BAD REQUEST\n\nInvalid HTTP version'
        if first_header_fields[0] != 'GET':
            return 'HTTP/1.1 400 BAD REQUEST\n\nInvalid method'
        filename = first_header_fields[1]

    else:
        return 'HTTP/1.1 400 BAD REQUEST\n\n'

    # Remove slash from file name if present
    if filename is not None and filename[0] == "/":
        # Default to test.html
        if (filename == '/'):
            filename = 'test.html'
        else:
            filename = filename[1:]

    # Parse the headers into a key value set to access later
    header_set = {}
    headers = headers[1:]
    for header in headers:
        if not header:
            continue
        key, value = header.split(':', 1)
        header_set[key] = value

    try:
        # Based on https://github.com/python/cpython/blob/master/Lib/http/server.py
        if 'If-Modified-Since' in header_set:
            file_descriptor = os.open(filename, os.O_RDWR | os.O_CREAT)
            file_status = os.fstat(file_descriptor)
            try:
                if_modified_since = email.utils.parsedate_to_datetime(header_set["If-Modified-Since"])
            except (TypeError, IndexError, OverflowError, ValueError):
                pass
            else:
                if if_modified_since.tzinfo is None:
                    if_modified_since = if_modified_since.replace(tzinfo=datetime.timezone.utc)
                if if_modified_since.tzinfo is datetime.timezone.utc:
                    last_modif = datetime.datetime.fromtimestamp(file_status.st_mtime, datetime.timezone.utc)
                    last_modif = last_modif.replace(microsecond=0)
                    print(last_modif)
                    print(if_modified_since)
                    if last_modif <= if_modified_since:
                        return 'HTTP/1.1 304 NOT MODIFIED\n\n'

        file_reader = open(filename)
        content = file_reader.read()
        file_reader.close()
        return 'HTTP/1.1 200 OK\n\n' + content

    except FileNotFoundError:
        return 'HTTP/1.1 404 NOT FOUND\n\nFile Not Found'

    except TimeoutError:
        return 'HTTP/1.1 408 REQUEST TIME OUT\n\n Request Timed Out'

    except TypeError:
        pass

# Following tutorial on https://www.techbeamers.com/python-tutorial-write-multithreaded-python-server/
class ClientThread(Thread):

    def __init__(self, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        print("[+] New server socket thread started for " + ip + ":" + str(port))

    def run(self):
        while True:
            request = clientConn.recv(1024).decode()
            print(request)
            response = handle_request(request)
            print ("Server received request:" + request)
            clientConn.sendall(response.encode())  # echo
            clientConn.close()


# Multithreaded Python server : TCP Server Socket Program Stub
IP = '0.0.0.0'
PORT = 2000
BUFFER_SIZE = 20
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind server
server.bind((IP, PORT))
server.listen(4)
threads = []

while True:
    # Wait for client requests
    print("Multithreaded Python server : Waiting for connections from TCP clients...")
    (clientConn, (ip, port)) = server.accept()
    newThread = ClientThread(ip, port)

    # Create new Thread
    newThread.start()
    threads.append(newThread)

# Join for each of the threads
for t in threads:
    t.join()
