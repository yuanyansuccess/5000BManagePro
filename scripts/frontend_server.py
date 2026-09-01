import sys
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    # 默认服务 frontend/ 子目录
    root = sys.argv[2] if len(sys.argv) > 2 else "frontend"
    if os.path.isdir(root):
        os.chdir(root)
    httpd = ThreadingHTTPServer(("", port), NoCacheHandler)
    print("frontend no-cache server on http://127.0.0.1:%d/ serving %s" % (port, os.getcwd()))
    httpd.serve_forever()