import os

from alexa_youtube_webserver.config.config import config
import tornado.ioloop
import tornado.web
import yaml
from asgiref.sync import sync_to_async

from alexa_youtube_webserver.lambda_function.lambda_function import lambda_handler


class AlexaYTubeHandler(tornado.web.RequestHandler):
    async def post(self):
        data = tornado.escape.json_decode(self.request.body)
        print(f"Data: {data}")
        result = await sync_to_async(lambda_handler)(data, None)
        print(f"Result: {result}")
        if result:
            self.write(result)


def make_app():
    return tornado.web.Application([
        (r"/alexaytube", AlexaYTubeHandler),
    ])


if not config.get("certfile") or not config.get("keyfile"):
    raise Exception("Please configure SSL certificate and key location in your config")

app = make_app()
http_server = tornado.httpserver.HTTPServer(app, ssl_options={
    "certfile": config.get("certfile"),
    "keyfile": config.get("keyfile"),
}
                                            )
http_server.listen(config.get("port", 443))
tornado.ioloop.IOLoop.current().start()
