"""Integration-like tests with an in-process fake ComfyUI, no GPU required."""
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import server as app_server

ID = '11111111-2222-3333-4444-555555555555'
last_graph = None


class FakeComfy(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send_json(self, value):
        raw = json.dumps(value).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/models/checkpoints':
            return self.send_json(['animagine-xl-4.0-opt.safetensors'])
        if self.path == '/models/loras':
            return self.send_json([])
        if self.path == '/system_stats':
            return self.send_json({'devices':[{'name':'Fake GPU'}]})
        if self.path == f'/history/{ID}':
            return self.send_json({ID:{'outputs':{'7':{'images':[{'filename':'LocalStudio_00001_.png','subfolder':'','type':'output'}]}}, 'status':{'status_str':'success'}}})
        return self.send_json({})

    def do_POST(self):
        global last_graph
        size = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(size)
        if self.path == '/prompt':
            last_graph = json.loads(data)['prompt']
            return self.send_json({'prompt_id':ID})
        return self.send_json({})


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.comfy = ThreadingHTTPServer(('127.0.0.1',0),FakeComfy)
        app_server.COMFY = f'http://127.0.0.1:{cls.comfy.server_port}'
        cls.studio = ThreadingHTTPServer(('127.0.0.1',0),app_server.Handler)
        cls.comfy_thread=threading.Thread(target=cls.comfy.serve_forever,daemon=True)
        cls.studio_thread=threading.Thread(target=cls.studio.serve_forever,daemon=True)
        cls.comfy_thread.start();cls.studio_thread.start()
        cls.url=f'http://127.0.0.1:{cls.studio.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.studio.shutdown();cls.comfy.shutdown()
        cls.studio.server_close();cls.comfy.server_close()

    def get(self,path):
        with urlopen(self.url+path,timeout=5) as r:
            return json.loads(r.read())

    def post(self,path,data):
        raw=json.dumps(data).encode('utf8')
        req=Request(self.url+path,data=raw,headers={'Content-Type':'application/json'},method='POST')
        with urlopen(req,timeout=5) as r:
            return json.loads(r.read())

    def test_status_and_models(self):
        self.assertTrue(self.get('/api/status')['ready'])
        self.assertEqual(len(self.get('/api/models')['checkpoints']),1)

    def test_generate_job(self):
        result=self.post('/api/generate',{'checkpoint':'animagine-xl-4.0-opt.safetensors','prompt':'adult woman portrait'})
        self.assertEqual(result['id'],ID)
        self.assertEqual(last_graph['7']['class_type'],'SaveImage')
        job=self.get('/api/job?id='+ID)
        self.assertEqual(job['state'],'done')
        self.assertIn('LocalStudio_',job['images'][0])


if __name__=='__main__':
    unittest.main()
