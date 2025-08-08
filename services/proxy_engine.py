import asyncio
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.addons import core

class SimpleProxy:
    def __init__(self, listen_host="0.0.0.0", listen_port=8081):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.master = None

    async def start(self):
        opts = options.Options(listen_host=self.listen_host, listen_port=self.listen_port)
        self.master = DumpMaster(opts, with_termlog=False, with_dumper=False)
        self.master.addons.add(core.Core())
        await asyncio.to_thread(self.master.run)

    async def shutdown(self):
        if self.master:
            await asyncio.to_thread(self.master.shutdown)

proxy_engine = SimpleProxy()
