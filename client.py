from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory


class MyClientProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))
        print('Response from Server:', response)

    def onConnecting(self, transport_details):
        print("Connecting; transport details: {}".format(transport_details))
        return None  # ask for defaults

    def onOpen(self):
        print("WebSocket connection open.")

        def hello():
            self.sendMessage("Hello, world!".encode('utf8'))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            #self.factory.reactor.callLater(1, hello)

        # start sending messages every second ..
        hello()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        reactor.disconnectAll()
        reactor.stop()

if __name__ == '__main__':

    import sys

    from twisted.python import log
    d = dir(reactor)
    with open('reactor_props.txt', 'w') as f:
        for x in d:
            f.write(x + '\n')
    print('Wrote the properties of reactor.')
    #log.startLogging(sys.stdout)

    factory = WebSocketClientFactory("ws://127.0.0.1:9000/?fn=aqeel&ln=abbas")
    factory.protocol = MyClientProtocol

    reactor.connectTCP("127.0.0.1", 9000, factory)
    reactor.run()
