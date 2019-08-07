from aiohttp.web import RouteTableDef, Request, Response, HTTPFound, json_response
from aiohttp_jinja2 import template, setup as jinja2_setup
from assets import CustomApp, Database
from jinja2 import FileSystemLoader

# Setup routes
routes = RouteTableDef()

# Auth decorator
def admin_required(f):
    """A custom decorator based off ``CustomApp.admin_required``
    that does pretty much the exact same thing but doesn't need
    to have the class initialised first"""
    
    def predicate(request: Request):
        #return f(request)
        
        # Grab the required data
        app = request.app
        token = request.cookies.get("token")
        tokens = app.tokens
        rtokens = {v:k for k,v in tokens.items()}
        user = rtokens.get(token)

        # Actually check the auth
        if user is None:
            return json_response(dict(
                status= 401,
                message= "You need to be logged in to access this resource"
            ))
        with Database() as db:
            if not any((db.is_admin(user), token==app.master_token)):
                return json_response(dict(
                    status= 403,
                    message= "You do not have sufficient permissions to access this resource"
                ))

        # It seems we passed ¯\_(ツ)_/¯
        return f(request)
    return predicate

# Admin Routes
@routes.get("/")
@template("admin/aindex.jinja")
@admin_required
async def index(request: Request):
    return dict(request= request)

@routes.get("/quit")
@admin_required
async def quit(request: Request):
    await request.app.shutdown()
    await request.app.cleanup()
    raise KeyboardInterrupt("Web shut down")

@routes.get("/log")
@admin_required
async def log(request: Request):
    with open("temp/website.log") as f:
        return Response(text= "\n".join(f.readlines()))

@routes.get("/log/clear")
@admin_required
async def log_clear(request: Request):
    with open("temp/website.log", "w") as f:
        return HTTPFound("/a/log")

@routes.get("/viewusers")
@template("admin/aviewusers.jinja")
@admin_required
async def viewusers(request: Request):
    print(request.app.usercreds.items())
    return dict(request= request, usercreds= request.app.usercreds)

    if "suspended" in request.query:
        resp = sorted(resp, key= lambda k: k["suspended"], reverse= True)
    if "admin" in request.query:
        resp = sorted(resp, key= lambda k: k["admin"], reverse= True)

    return dict(usercreds= resp, request= request)

@routes.get("/test")
@admin_required
async def test(request: Request):
    return Response(text= "yayeet!")

# Create the app
AdminApp = CustomApp()
AdminApp.add_routes(routes)

# Run the app if desired
if __name__ == "__main__":
    AdminApp.router.add_static("/assets", "./static")
    jinja2_setup(AdminApp, loader=FileSystemLoader("./templates"))
    AdminApp.run(port= 4321)
