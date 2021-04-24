from aiohttp.web import HTTPException, HTTPFound, Request, Response
from aiohttp.web import middleware
from aiohttp_jinja2 import render_template

# Middlewares
@middleware
async def error_middleware(request: Request, handler):
    handled_errors = [403, 404]

    try:
        response = await handler(request)
        if response.status not in handled_errors:
            return response
        message = response.message
    except HTTPException as ex:
        if ex.status not in handled_errors:
            raise
        message = ex.reason

    return render_template("_base.jinja", request, dict(request=request))


@middleware
async def mobile_token_middleware(request: Request, handler):
    token = request.cookies.get("sleuth_token")

    if all((token, not request.url.query.get("token"), await request.app.is_mobile(request))):
        return HTTPFound(str(request.rel_url) + f"?token={token}")
    return await handler(request)


# Helper functions
async def is_mobile(request: Request):
    """Returns ``True`` if the request was mobile, else ``False``"""
    return request.app.device(request.headers["User-Agent"]).parse().is_mobile()


# Exports
Middlewares = [
    error_middleware,
    mobile_token_middleware,
]
