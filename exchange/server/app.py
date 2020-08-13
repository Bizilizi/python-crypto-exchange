from aiohttp import web

from .helper import status_pages
from .routing import routes


async def application_factory() -> web.Application:
    app = web.Application(middlewares=[status_pages])
    app.add_routes(routes)
    return app
