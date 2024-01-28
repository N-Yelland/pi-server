#!/usr/bin/env python

import asyncio
import socketio
import ssl

from aiohttp import web


def html_response(path):
    with open(path, "r") as f:
        resp = web.Response(text=f.read(), content_type="text/html")
    return resp


async def run_server():
    sio = socketio.AsyncServer(namespaces="*", async_mode="aiohttp")
    app = web.Application()
    sio.attach(app)

    routes = web.RouteTableDef()

    @routes.get("/")
    async def get_handler(request):
        print("New connection!")
        return html_response("client/index.html")

    routes.static("/", "client")
    app.router.add_routes(routes)

    @sio.event(namespace="/")
    async def connect(sid, environ, auth):
        request = environ["aiohttp.request"]
        ip_address = request.remote

        print(f"New connection from {ip_address}")
        with open("message_log", "r") as f:
            await sio.emit("update", f.read().split("\n"), to=sid)
    
    @sio.on("message")
    async def message_handler(sid, data):
        message = data["message"]
        print(f"New message: {message}")
        with open("message_log", "a") as f:
            f.write(message + "\n")
        with open("message_log", "r") as f:
            await sio.emit("update", f.read().split("\n"))

    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain("certs/cert.pem", "certs/cert.key")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner=runner,
        port=12233,
        ssl_context=ssl_context
    )
    await site.start()
    print("Server running...")

    await asyncio.Event().wait()

if __name__ == "__main__":
    print("Starting server...")
    asyncio.run(run_server())
