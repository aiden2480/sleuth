"""
The file that serves static files from the root directory,
for a whole bunch of reasons like Google Crawling, Sitemaps, etc
"""
from aiohttp.web import Response, RouteTableDef, Request, StaticResource

# The thingo
FileRoutes = RouteTableDef()
handled_files = [
    "js/service-worker.js",
    "js/upup.min.js",
    "js/upup.sw.min.js",
    "robots.txt",
    "sitemap.xml",
]

# @FileRoutes.get("/{file}")
async def handler(request: Request):
    file = request.match_info["file"]
    if file not in handled_files:
        return
    with open(f"./static/{file}") as p:
        bits = str(request).split("/")
        url = f"https://{bits[2]}"


# Thingo routes
@FileRoutes.get("/service-worker.js")
async def sw(request):
    with open("./static/js/service-worker.js") as j:
        return Response(body=j.read(), content_type="application/javascript")


@FileRoutes.get("/upup.min.js")
async def upup(request):
    with open("./static/js/upup.min.js") as j:
        return Response(body=j.read(), content_type="application/javascript")


@FileRoutes.get("/upup.sw.min.js")
async def upup(request):
    with open("./static/js/upup.sw.min.js") as j:
        return Response(body=j.read(), content_type="application/javascript")


@FileRoutes.get("/robots.txt")
async def robotstxt(request):
    with open("./static/robots.txt") as r:
        bits = str(request.url).split("/")
        url = f"https://{bits[2]}"
        return Response(body=r.read().replace("[BASE]", url), content_type="text/plain")


@FileRoutes.get("/sitemap.xml")
async def sitemap(request):
    with open("./static/_sitemap.xml") as s:
        bits = str(request.url).split("/")
        url = f"https://{bits[2]}"
        return Response(
            body=s.read().replace("[BASE]", url), content_type="application/xml"
        )


@FileRoutes.get("/.htaccess")
async def htaccess(request):
    with open("./static/.htaccess") as h:
        return Response(body=h.read())
