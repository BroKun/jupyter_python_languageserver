import json
import logging
import subprocess
import threading

from tornado import ioloop, process, web, websocket, gen

from jsonrpc import streams


class LanguageServerWebSocketHandler(websocket.WebSocketHandler):
    """Setup tornado websocket handler to host an external language server."""

    writer = None

    def open(self, *args, **kwargs):
        # log.debug("Spawning pyls subprocess")

        # Create an instance of the language server
        proc = process.Subprocess(
            ['pyls'], #'-vvv'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

        # Create a writer that formats json messages with the correct LSP headers
        self.writer = streams.JsonRpcStreamWriter(proc.stdin)

        # Create a reader for consuming stdout of the language server. We need to
        # consume this in another thread
        def consume():
            # Start a tornado IOLoop for reading/writing to the process in this thread
            ioloop.IOLoop()
            reader = streams.JsonRpcStreamReader(proc.stdout)
            reader.listen(lambda msg: self.write_message(json.dumps(msg)))

        thread = threading.Thread(target=consume)
        thread.daemon = True
        thread.start()

    def on_message(self, message):
        """Forward client->server messages to the endpoint."""
        self.writer.write(json.loads(message))

    def check_origin(self, origin):
        return True
