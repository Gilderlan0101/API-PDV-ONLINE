import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Main import app
from starlette.middleware.wsgi import WSGIMiddleware

application = WSGIMiddleware(app)
