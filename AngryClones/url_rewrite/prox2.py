from twisted.internet import reactor
from twisted.web import http
from twisted.web.proxy import Proxy, ProxyRequest, ProxyClientFactory, ProxyClient
from ImageFile import Parser
from StringIO import StringIO

class InterceptingProxyClient(ProxyClient):
    def __init__(self, *args, **kwargs):
        ProxyClient.__init__(self, *args, **kwargs)
        self.image_replacing = None
        if 'INGAME_BIRDS_PIGS.png' in self.father.uri:
            print "REPLACING"
            self.image_replacing = True

    def handleHeader(self, key, value):
        if key == "Content-Length" and self.image_replacing:
            pass
        else:
            ProxyClient.handleHeader(self, key, value)

    def handleEndHeaders(self):
        if self.image_replacing:
            pass  # Need to calculate and send Content-Length first
        else:
            ProxyClient.handleEndHeaders(self)

    def handleResponsePart(self, buffer):
        if self.image_replacing:
            pass
        else:
            ProxyClient.handleResponsePart(self, buffer)

    def handleResponseEnd(self):
        if self.image_replacing:
            try:
                buffer = open("/Users/thouis/INGAME_BIRDS_PIGS.png").read()
            except:
                buffer = ""
            ProxyClient.handleHeader(self, "Content-Length", len(buffer))
            ProxyClient.handleEndHeaders(self)
            ProxyClient.handleResponsePart(self, buffer)
        ProxyClient.handleResponseEnd(self)

class InterceptingProxyClientFactory(ProxyClientFactory):
    protocol = InterceptingProxyClient

class InterceptingProxyRequest(ProxyRequest):
    protocols = {'http': InterceptingProxyClientFactory}
    ports = {"http" : 80}

class InterceptingProxy(Proxy):
    requestFactory = InterceptingProxyRequest

factory = http.HTTPFactory()
factory.protocol = InterceptingProxy

reactor.listenTCP(8000, factory)
reactor.run()
