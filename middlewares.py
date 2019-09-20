from aiohttp.web import HTTPException, Request, Response
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
async def internal_server_error_middleware(request: Request, handler):
    try:
        response = await handler(request)
        if response.status != 500:
            return response
        message = response.message
    except HTTPException as ex:
        if ex.status != 500:
            raise
        message = ex.reason

    return Response(text="Uh oh! Internal server error 😟")
    return render_template("_base.jinja", request, dict(request=request))


# Exports
Middlewares = [error_middleware, internal_server_error_middleware]
