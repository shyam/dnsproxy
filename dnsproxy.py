#!/usr/bin/env python
import signal
from maproxy.iomanager import IOManager
from maproxy.proxyserver import ProxyServer

g_IOManager = IOManager()

if __name__ == '__main__':
  # calls the "stop()" when asked to exit
  signal.signal(signal.SIGINT, lambda sig, frame: g_IOManager.stop())
  signal.signal(signal.SIGTERM, lambda sig, frame: g_IOManager.stop())

  # "server_ssl_options=True" means reverse proxy to server with TLS
  server = ProxyServer("1.1.1.1", 853, server_ssl_options = True)
  server.listen(53)
  g_IOManager.add(server)

  print("[dnsproxy] tcp://127.0.0.1:53 -> tcp+tls://1.1.1.1:853")
  # the next call to start() is blocking (thread=False)
  g_IOManager.start(thread = False)

  print("[dnsproxy] Stopping...")
  g_IOManager.stop(gracefully = True, wait = False)
  print("[dnsproxy] Stopped !")
