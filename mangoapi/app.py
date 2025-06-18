# mangoapi/app.py
from django.core.asgi import get_asgi_application
from starlette.routing import Mount
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from mangoapi.exceptions import MangoAPIError
from mangoapi.logging import setup_logger
from mangoapi.router import Router


logger = setup_logger()

class MangoAPI:
    def __init__(self, api_prefix="/api"):
        self.django_app = get_asgi_application()

        self.router = Router()
        self.api_prefix = api_prefix

        self._starlette_app = None
        self._build_app()

    def _build_app(self):
        try:
            starlette_routes = self.router.to_starlette_routes()
            mangoapi_app = Starlette(
                routes=starlette_routes,
                middleware=[Middleware(CORSMiddleware, allow_origins=["*"])],
            )
            routes = [
                Mount(self.api_prefix, app=mangoapi_app),
                Mount("/", app=self.django_app),
            ]
            self._starlette_app = Starlette(routes=routes)
        except Exception as e:
            logger.exception("Error while building MangoAPI app.")
            raise MangoAPIError()

    def include_router(self, other_router: Router):
        self.router.include_router(other_router)
        self._build_app()

    async def __call__(self, scope, receive, send):
        if self._starlette_app is None:
            self._build_app()
        await self._starlette_app(scope, receive, send)
