from aiohttp.web import HTTPException, Request
from aiohttp.web import middleware
from aiohttp_jinja2 import render_template

# Middlewares
@middleware
async def error_middleware(request: Request, handler):
    handled_errors = [403, 404, 500]

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


# Exports
Middlewares = [error_middleware]
