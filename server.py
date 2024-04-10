#!/usr/bin/env python

import asyncio
import socketio
import ssl
import traceback

from aiohttp import web
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from crossword import process_generate_request, BadRequest

pool = ProcessPoolExecutor(3)


def html_response(path):
    with open(path, "r") as f:
        resp = web.Response(text=f.read(), content_type="text/html")
    return resp


async def run_server(port):
    sio = socketio.AsyncServer(namespaces="*", async_mode="aiohttp")
    app = web.Application()
    sio.attach(app)

    routes = web.RouteTableDef()

    @routes.get("/")
    async def get_handler(request):
        print("New connection!")
        return html_response("client/index.html")
    
    @routes.get("/quizdle-builder")
    async def get_handler(request):
        print("New connection!")
        return html_response("quizdle-builder/index.html")
        
    # TODO: make this a POST request!
    @routes.get("/quizdle-builder/generate")
    async def post_handler(request: web.Request):
        try:
            if request.query.get("words") is None:
                return web.Response(text="Submit request by suffixing url with comma-separated list of words, e.g.:" + \
                    "\n\n\t" + \
                    "https://pi.nicyelland.com/quizdle-builder/generate?words=axolotl,bear,canary,dingo,elephant\n")
            words = [w.upper() for w in request.query.get("words").split(",")]
            print(f"Crossword Generation Request for {words}")
            
            return_json = (request.query.get("json") == "true")

            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(pool, partial(process_generate_request, json=return_json), words)
            return web.json_response(data)
        
        except TimeoutError:
            return web.Response(text=f"Request timed out! Try using words with fewer letters in common!\n")
        
        except BadRequest as e:
            return web.Response(text=f"Error: {e}\n")
        
        except Exception as e:
            return web.Response(text=f"Unhandled Error ({type(e).__name__}): " + \
                                f"{e}\n{''.join(traceback.format_tb(e.__traceback__))}\n")

    # These need to be in order of depth, starting with deepest?
    routes.static("/quizdle-builder", "quizdle-builder")
    routes.static("/", "client")

    app.router.add_routes(routes)

    @sio.event(namespace="/")
    async def connect(sid, environ, auth):
        request = environ["aiohttp.request"]
        ip_address = request.remote
        print(f"New connection from {ip_address}")
    
    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain("certs/cert.pem", "certs/cert.key")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner=runner,
        port=port,
        ssl_context=ssl_context
    )
    await site.start()
    print("Server running...")

    await asyncio.Event().wait()

if __name__ == "__main__":
    print("Starting server...")
    asyncio.run(run_server())
