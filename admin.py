from aiohttp.web import RouteTableDef, Request, Response, HTTPFound, json_response
from aiohttp_jinja2 import template
from assets import CustomApp, Database

# Setup routes
routes = RouteTableDef()

# Auth decorator
def admin_required(f):
    """A custom decorator based off ``CustomApp.admin_required``
    that does pretty much the exact same thing but doesn't need
    to have the class initialised first"""

    def predicate(request: Request):
        # return f(request)

        # Grab the required data
        app = request.app
        token = request.cookies.get("sleuth_token")
        tokens = app.tokens
        rtokens = {v: k for k, v in tokens.items()}
        user = rtokens.get(token)

        # Actually check the auth
        if user is None:
            return json_response(
                dict(
                    status=401,
                    message="You need to be logged in to access this resource",
                )
            )
        with Database() as db:
            if not any((db.is_admin(user), token == app.master_token)):
                return json_response(
                    dict(
                        status=403,
                        message="You do not have sufficient permissions to access this resource",
                    )
                )

        # It seems we passed ¯\_(ツ)_/¯
        return f(request)

    return predicate


# Admin Routes
@routes.get("/")
@template("admin/aindex.jinja")
@admin_required
async def index(request: Request):
    return dict(request=request)


@routes.get("/quit")
@admin_required
async def quit(request: Request):
    await request.app.shutdown()
    await request.app.cleanup()
    raise KeyboardInterrupt("Web shut down")


@routes.get("/viewusers")
@template("admin/aviewusers.jinja")
@admin_required
async def viewusers(request: Request):
    return dict(request=request, usercreds=request.app.usercreds)

    if "suspended" in request.query:
        resp = sorted(resp, key=lambda k: k["suspended"], reverse=True)
    if "admin" in request.query:
        resp = sorted(resp, key=lambda k: k["admin"], reverse=True)

    return dict(usercreds=resp, request=request)


# Create the app
AdminApp = CustomApp()
AdminApp.add_routes(routes)

# Run the app if desired
if __name__ == "__main__":
    from aiohttp_jinja2 import setup as jinja2_setup
    from jinja2 import FileSystemLoader

    AdminApp.router.add_static("/static", "./static")
    jinja2_setup(AdminApp, loader=FileSystemLoader("./templates"))
    AdminApp.run(port=4321)
