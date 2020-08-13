from aiohttp import web
from exchange.server.app import application_factory


if __name__ == "__main__":
    web.run_app(application_factory(), port=8080)
