import os
import click
import json
import uuid
import logging
import importlib.util
from tornado.ioloop import IOLoop
from tornado.escape import json_decode
from tornado.web import Application, RequestHandler


def load_filename(path, specname=None):
    spec = importlib.util.spec_from_file_location(specname or str(uuid.uuid4()).replace("-", ""), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_pyfunc(script, func):
    spec = importlib.util.spec_from_file_location(func, script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, func)


class SimpleAPIHandler(RequestHandler):
    def initialize(self, func):
        self.func = func

    def post(self, *args, **kwargs):
        self.write(json.dumps(self.func(*args, **json_decode(self.request.body))))


FORMAT = '[%(asctime)s] [%(name)s] - %(levelname)s - [%(message)s]'


class PingHandler(RequestHandler):
    def get(self, *args, **kwargs):
        self.write(f"Service live on {self.request.uri}.")


class SageMakerApplication(Application):
    """
    A utility class for setting up a SageMaker-compliant Tornado application.
    """

    def __init__(self, handler, *args, config: dict=None, **kwargs):

        handlers = [(r"/invocations", handler, config or {}),
                    (r"/ping", PingHandler)]

        super().__init__(handlers, *args, **kwargs)

    def run(self, *args, ioloop=None, **kwargs):
        self.listen(*args, **kwargs)

        if ioloop is None:
            IOLoop.current().start()
        else:
            ioloop.start()


logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT
)


APPS = {
    "sagemaker": SageMakerApplication
}


HANDLERS = {
    "simple": SimpleAPIHandler
}


@click.command()
@click.option("-s", "--script", required=True, help="The source file (containing target function).")
@click.option("-f", "--func", required=True, help="The target function.")
@click.option("-v", "--variant", default="sagemaker", help="The Orion/Tornado application variant to use.")
@click.option("-h", "--handler", default="simple", help="The Orion/Tornado handler to use.")
@click.option("-p", "--port", default=8080, help="The port to expose.")
@click.option("-a", "--address", default="0.0.0.0", help="The address to host the server on.")
def serve(variant: str,
          script: str,
          func: str,
          handler: str="simple",
          port: int=8080,
          address: str="0.0.0.0",
          **kwargs):

    """
    Serve a target function in a target script behind a Tornado Server.
    Parameters
    ----------
    variant: str
        The Tornado Application (Server) variant to use.
    script: str
        The filepath to the target script to use.
    func: str
        The name of the target function to use.
    handler: str
        The handler variant to use.
    port: int
        The port for the server.
    address: str
        The host address for the server.
    kwargs: dict
        Optional arguments that will be passed to the 'handler' class provided.
    """

    variant = APPS[variant]
    handler = HANDLERS[handler]

    if os.path.exists(script):
        ext = os.path.splitext(script)[1]
        if ext == ".R":
            func = load_rfunc(script, func)
        elif ext == ".py":
            func = load_pyfunc(script, func)
        else:
            raise ValueError(f"Cannot parse files with extension '{ext}'.")

        app = variant(handler, config=dict(func=func, **kwargs))
        app.run(address=address, port=port)

    else:
        raise FileNotFoundError(f"Cannot find script: {script}")


if __name__ == "__main__":
    serve()
