from aiohttp.web import RouteTableDef, Request, Response, HTTPFound, json_response
from aiohttp_jinja2 import template
from assets import CustomApp, Database

# Setup routes
AdminRoutes = RouteTableDef()

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
@AdminRoutes.get("/")
@template("admin/aindex.jinja")
@admin_required
async def index(request: Request):
    return dict(request=request)


@AdminRoutes.get("/viewusers")
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
AdminApp.add_routes(AdminRoutes)
