from aiohttp import web

from .routing import routes


async def application_factory() -> web.Application:
    app = web.Application()
    app.add_routes(routes)
    return app
