from docker import Client
from io import BytesIO
from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid.response import Response
from requests.exceptions import ReadTimeout
from urllib.parse import unquote_plus
from wsgiref.simple_server import make_server

import tarfile


IP = '0.0.0.0'
PORT = 8000

cli = Client(base_url='unix://var/run/docker.sock')


def compilecode(request):
    if request.method == 'OPTIONS':
        return Response('Ok')

    if request.content_type == 'application/json':
        data = request.json
        code = data['code']
        lang = data['lang'].lower()
        stdin = data['stdin']
    else:
        code = unquote_plus(request.POST['code'])
        stdin = unquote_plus(request.POST['stdin'])
        lang = request.POST['lang'].lower()

    host_config = cli.create_host_config(mem_limit='128m', network_mode='none')

    if lang not in ['python', 'c++', 'python2', 'csharp', 'javascript']:
        return Response('Invalid language')

    timeout = 5

    if lang == 'python':
        image = 'python:3.5'
        timeout = 10
        runscript = """#!/bin/sh
        cat stdin.txt | python code.txt
        """
    elif lang == 'c++':
        image = 'gcc:4.9'
        runscript = """#!/bin/sh
        set -e
        g++ -std=gnu++11 -lm -xc++ code.txt
        cat stdin.txt | ./a.out
        """
    elif lang == 'python2':
        image = 'python:2.7'
        timeout = 10
        runscript = """#!/bin/sh
        cat stdin.txt | python code.txt
        """
    elif lang == 'csharp':
        image = 'mono:4.2'
        runscript = """#!/bin/sh
        set -e
        mcs code.txt
        cat stdin.txt | mono code.exe
        """
    elif lang == 'javascript':
        image = 'node:5.9'
        timeout = 10
        runscript = """#!/bin/sh
        cat stdin.txt | node code.txt
        """

    # Create tar for code, stdin, runscript (strings)
    tar_file = BytesIO()
    tar = tarfile.open(fileobj=tar_file, mode='w')

    code_bytes = bytearray(code, encoding='utf-8')
    code_info = tarfile.TarInfo('code.txt')
    code_info.size = len(code_bytes)
    tar.addfile(code_info, BytesIO(code_bytes))

    stdin_bytes = bytearray(stdin, encoding='utf-8')
    stdin_info = tarfile.TarInfo('stdin.txt')
    stdin_info.size = len(stdin_bytes)
    tar.addfile(stdin_info, BytesIO(stdin_bytes))

    runscript_bytes = bytearray(runscript, encoding='utf-8')
    runscript_info = tarfile.TarInfo('runscript.sh')
    runscript_info.mode = int('0755', 8)
    runscript_info.size = len(runscript_bytes)
    tar.addfile(runscript_info, BytesIO(runscript_bytes))

    tar.close()

    c = cli.create_container(
        image=image,
        host_config=host_config,
        command='/runscript.sh')

    cli.put_archive(c, '/', tar_file.getvalue())
    cli.start(c)

    try:
        cli.wait(c, timeout=timeout)
    except ReadTimeout:
        # Timed out
        return {'output': None, 'error': 'Timed out'}
    else:
        output = cli.logs(c).decode(encoding='utf-8')
        if cli.inspect_container(c)['State']['ExitCode'] != 0:
            return {'output': output, 'error': 'Compilation failed'}

        return {'output': output, 'error': None}
    finally:
        cli.remove_container(c, force=True)


def add_cors_headers_response_callback(event):
    def cors_headers(request, response):
        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
            'Access-Control-Allow-Headers':
                'Origin, Content-Type, Accept, Authorization',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '1728000',
        })
    event.request.add_response_callback(cors_headers)


if __name__ == '__main__':
    config = Configurator()
    config.add_subscriber(add_cors_headers_response_callback, NewRequest)
    config.add_route('compilecode', '/compile/')
    config.add_view(compilecode, route_name='compilecode', renderer='json')
    app = config.make_wsgi_app()
    server = make_server(IP, PORT, app)
    print('Starting server at http://%s:%s' % (IP, PORT))
    server.serve_forever()
