from socket import *
import email.utils
import os, sys
import datetime
import time


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

    start = time.time()
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
        #Sleep for 2 seconds. Uncomment to replicate 408 time out
        #time.sleep(2)
        
    except FileNotFoundError:
        return 'HTTP/1.1 404 NOT FOUND\n\nFile Not Found'

    except TypeError:
        pass

    #Server limits the process time for each request to only 1 second
    end = time.time()
    if end - start > 1:
                return  'HTTP/1.1 408 REQUEST TIMEOUT\n\n 408 REQUEST TIMED OUT'

    return 'HTTP/1.1 200 OK\n\n' + content


# Set up host and socket
HOST = '0.0.0.0'
PORT = 5000
server = socket(AF_INET, SOCK_STREAM)
server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Bind server
server.bind((HOST, PORT))
server.listen(1)
print('Listening on port %s ...' % PORT)

while True:
    # Wait for client requests
    clientConn, clientAddr = server.accept()

    # Get the client request
    request = clientConn.recv(1024).decode()
    print(request)

    response = handle_request(request)
    clientConn.sendall(response.encode())

    clientConn.close()

server.close()
