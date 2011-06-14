from twisted.internet import reactor
from twisted.web import http
from twisted.web.proxy import Proxy, ProxyRequest, ProxyClientFactory, ProxyClient
from ImageFile import Parser
from StringIO import StringIO
import threading
import os.path
import urllib

cachedir = 'cache'
replacedir = 'replace'

def cache_file(uri):
    if not 'chrome.angrybirds.com' in uri:
        return None
    return os.path.join(cachedir, uri.split('chrome.angrybirds.com')[-1].replace('/', '_'))

def replace_file(uri):
    if not 'chrome.angrybirds.com' in uri:
        return None
    replacement = os.path.join(replacedir, uri.split('chrome.angrybirds.com')[-1].replace('/', '_'))
    if os.path.exists(replacement):
        return replacement
    return None

class InterceptingProxyClient(ProxyClient):
    def __init__(self, *args, **kwargs):
        ProxyClient.__init__(self, *args, **kwargs)
        self.replacing = None
        cache_path = cache_file(self.father.uri)
        replace_path = replace_file(self.father.uri)
        if cache_path and not os.path.exists(cache_path):
            print "FETCHING", cache_path
            t = threading.Thread(target=lambda:urllib.urlretrieve(self.father.uri, cache_path))
            t.start()
        if replace_path:
            print "replacing %s with %s" % (self.father.uri, replace_path)
            self.replacing = replace_path

    def handleHeader(self, key, value):
        if key == "Content-Length" and self.replacing is not None:
            pass
        if key == "Content-Encoding" and value == 'gzip' and self.replacing is not None:
            pass
        else:
            ProxyClient.handleHeader(self, key, value)

    def handleEndHeaders(self):
        if self.replacing is not None:
            pass  # Need to calculate and send Content-Length first
        else:
            ProxyClient.handleEndHeaders(self)

    def handleResponsePart(self, buffer):
        if self.replacing is not None:
            pass
        else:
            ProxyClient.handleResponsePart(self, buffer)

    def handleResponseEnd(self):
        if self.replacing is not None:
            try:
                buffer = open(self.replacing).read()
            except:
                print "FAIL", self.replacing
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
