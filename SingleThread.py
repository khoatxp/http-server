from socket import *
import email.utils
import os, sys
import datetime

def handle_request(request):
    headers = request.split('\r\n')

    #Get the first header for filename information
    filename = None
    first_header_fields = headers[0].split(" ")
    if len(first_header_fields) > 1:
        filename = first_header_fields[1]

    #Remove slash from file name if present
    if filename is not None and filename[0] == "/":
        #Default to test.html
        if(filename == '/'):
            filename = 'test.html'
        else:
            filename = filename[1:]

    #Parse the headers into a key value set to access later
    header_set = {}
    headers = headers[1:]
    for header in headers:
        if not header:
            continue
        key, value = header.split(':',1)
        header_set[key] = value


    try:
        #Based on https://github.com/python/cpython/blob/master/Lib/http/server.py
        if 'If-Modified-Since' in header_set:
            file_descriptor = os.open( filename, os.O_RDWR|os.O_CREAT )
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

    #TODO: implement 400 Bad Request 



#Set up host and socket
HOST = '0.0.0.0'
PORT = 5000
server = socket(AF_INET, SOCK_STREAM)
server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

#Bind server
server.bind((HOST, PORT))
server.listen(1)
print('Listening on port %s ...' % PORT)

while True:
    #Wait for client requests
    clientConn, clientAddr = server.accept()

    #Get the client request
    request = clientConn.recv(1024).decode()

    response = handle_request(request)
    clientConn.sendall(response.encode())

    clientConn.close()

server.close()