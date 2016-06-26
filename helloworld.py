import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class InfoHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello again, world")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/hello", InfoHandler)
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
    
                                                                                              
