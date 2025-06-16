# 🍋 MangoAPI

**MangoAPI** is a lightweight meta-framework that lets you build modern, clean and asynchronous APIs inside a traditional Django project.

It integrates [Starlette](https://www.starlette.io/) for async routing, while preserving Django’s admin, ORM, and all core functionality.

---

## 🚀 Features

- Clean sintaxis.
- Powered by Starlette for async support.
- Fully compatible with Django admin, ORM, and views.
- Minimal and zero-boilerplate setup.

---

## 🔧 Django Integration

* Your Django project continues to work as usual (`/admin`, ORM, templates).
* Async routes are automatically mounted under `/api`.

---

## 🎯 Why MangoAPI?

Because you want the best of both worlds:

* Django’s power and ecosystem.
* The speed and modernity of async APIs.

---

## ⚙️ Installation

```bash
pip install mangoapi
````

---

## 🧪 Quick Example

1- Create a django project:
```bash
django-admin startproject project .
````

2- Create a api django app:
```bash
python3 manage.py startapp appname
````

3- Add de app in your settings:
```python
# project/settings.py
INSTALLED_APPS = [
    ....

    "api",
]
````

4- Create inside your project directory a api.py file:
```python
# project/api.py
from mangoapi import MangoAPI
from api.routes.hello import router as hello_router

app = MangoAPI()
app.include_router(hello_router)
````

5- Delete all in asgi.py and add te MangoAPI app inside:
```python
from mangoapi_demo.api import app

application = app
````

6- Create a new endpoint
```python
# api/routes/hello.py
from mangoapi import Router

router = Router(prefix="/hello")

@router.get("/")
async def say_hello(name: str = "world"):
    return {"message": f"Hello {name} 👋"}
````

---

## 👤 Author

Built by Leandro Carriego(https://github.com/leandrocarriego)

---

## 📄 License

[MIT](LICENSE)
