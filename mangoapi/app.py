# mangoapi/app.py
import os

import django
from django.core.asgi import get_asgi_application
from starlette.routing import Mount
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from mangoapi.router import Router


class MangoAPI:
    """
    Clase que integra MangoAPI (Starlette) con Django,
    montando MangoAPI en `api_prefix` y Django en la raíz.

    Permite agregar rutas estilo FastAPI y mantener el admin y ORM Django.
    """

    def __init__(self, api_prefix="/api"):
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE",
            os.getenv("DJANGO_SETTINGS_MODULE", "project.settings"),
        )
        django.setup()
        self.django_app = get_asgi_application()

        self.router = Router()
        self.api_prefix = api_prefix

        self._starlette_app = None
        self._build_app()

    def _build_app(self):
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

    def get(self, path, status_code=200):
        return self.router.get(path, status_code)

    def post(self, path, status_code=200):
        return self.router.post(path, status_code)

    def include_router(self, other_router: Router):
        self.router.include_router(other_router)
        self._build_app()  # reconstruir para actualizar rutas

    async def __call__(self, scope, receive, send):
        if self._starlette_app is None:
            self._build_app()
        await self._starlette_app(scope, receive, send)
