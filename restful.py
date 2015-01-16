import sys
import os
import ssl
import time
import cgi
import pwd
import grp
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class RestfulHTTPRequestHandler(SimpleHTTPRequestHandler):
    certkey = 'cert.key'
    certfile = 'cert.crt'
    rootdir = 'public/'
    realm = 'authentication required'
    credential = ('admin', 'admin')

    def __init__(self, request, client_address, server):
        request = ssl.wrap_socket(request, keyfile=self.certkey, certfile=self.certfile, server_side=True)
        return SimpleHTTPRequestHandler.__init__(self, request, client_address, server)

    def version_string(self):
        return 'restful'

    def send_head(self):
        if not self.authenticate():
            return

        if self.path == '/post':
            return self.post_form()

        return SimpleHTTPRequestHandler.send_head(self)

    def post_form(self):
        f = StringIO()
        f.write("""<!DOCTYPE html>
<title>POST form</title>
<form method="post" action="/put" enctype="multipart/form-data">
<p><input type="file" name="file">
<input type="submit" value="PUT"></p>
</form>
<form method="post" action="/delete">
<p><input type="text" size="80" name="url" value="https://">
<input type="submit" value="DELETE">
</form>
""")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def do_POST(self):
        if not self.authenticate():
            return

        if self.path == '/put':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            item = form['file']
            if item.file:
                path = self.translate_path('/' + item.filename)
                with open(path, 'wb') as f:
                    self.copyfile(item.file, f)
                self.send_response(302)
                self.send_header('Location', "https://%s/" % self.headers['Host'])
                self.send_header('Content-Length', '0')
                self.end_headers()
            else:
                self.send_error(400)
        elif self.path == '/delete':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            url = form['url'].value
            path = '/' + url.split('/', 3)[3]
            path = self.translate_path(path)
            if os.path.isfile(path):
                os.remove(path)
                self.send_response(302)
                self.send_header('Location', "https://%s/" % self.headers['Host'])
                self.send_header('Content-Length', '0')
                self.end_headers()
            else:
                self.send_error(404)
        else:
            self.send_error(405)

    def do_PUT(self):
        if not self.authenticate():
            return

        path = self.translate_path(self.path)
        if os.path.exists(os.path.dirname(path)):
            with open(path, 'wb') as f:
                content_length = int(self.headers['Content-Length'])
                data = self.rfile.read(content_length)
                f.write(data)

            new_url = "https://%s%s" % (self.headers['Host'], self.path)
            self.send_response(201)
            self.send_header('Location', new_url)
            self.end_headers()
        else:
            self.send_error(403)

    def do_DELETE(self):
        if not self.authenticate():
            return

        path = self.translate_path(self.path)
        if os.path.isfile(path):
            os.remove(path)
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404)

    def authenticate(self):
        auth = self.headers.get('Authorization', '')
        tokens = auth.split(None, 2)

        if len(tokens) == 2 and tokens[0].upper() == 'BASIC':
            t = tokens[1].decode('base64').split(':')
            if tuple(t[:2]) == self.credential:
                return True

        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="%s"' % self.realm)
        self.send_header('Content-Length', 0)
        self.end_headers()
        return False

    def translate_path(self, path):
        path = "%s/%s" % (self.rootdir.rstrip('/'), path.replace('../', ''))
        return SimpleHTTPRequestHandler.translate_path(self, path)


def drop_priv(user='nobody', group='nogroup'):
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    groups = []

    try:
        os.setgroups([])
        os.setgid(gid)
        os.setuid(uid)
    except OSError as e:
        print >>sys.stderr, "must be root!"
        sys.exit(1)


def test(HandlerClass = RestfulHTTPRequestHandler, ServerClass = BaseHTTPServer.HTTPServer, protocol="HTTP/1.1"):
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 10443
    server_address = ('', port)

    HandlerClass.protocol_version = protocol
    httpd = ServerClass(server_address, HandlerClass)
    drop_priv()

    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()


if __name__ == '__main__':
    test()
