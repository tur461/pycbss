import CommonProperties as CP
import DPEntity as dpe
from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

cpr = None

def printLists():
    CP.printLens(cpr)
    CP.printAll(cpr)

class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, req):
        print(f'Client connecting: {req.peer}')
        self.ID = None
        self.Name = None
        self.Desig = None
        self.dynmkId = None
        self.PidList = set()
        self.IsConnected = False
        self.IsDuplicate = False

    def onOpen(self):
        #print('QueryString Params:', self.http_request_params)
        mParam = CP.getParams(self.http_request_params)
        if mParam is None:
            print('mParam is None, Closing Connection')
            CP.closeCon(self, 'Check Your Query String Params')
            return
        
        if mParam['typ'] == 'm':
            self.ID = str(mParam['id'])
            self.Name = mParam['name']
            self.Desig = mParam['desig']
            self.IsConnected = True
            print(f'Connected to {self.Desig} {self.Name} ID: {self.ID}')
            if mParam['from'] == 'doctor':
                if not CP.addConnectedDoctorId(cpr, self.ID):
                    # log here
                    rz = f'Already Connected to this Doctor at {CP.getDocConDetails(cpr, self.ID).peer}'
                    print(rz)
                    self.IsDuplicate = True
                    CP.closeCon(self, rz)
                    return
                CP.addPidList_doctor(self, mParam['pids'])
                CP.handleDocConOpen(cpr, self)
            elif mParam['from'] == 'patient':
                self.dynmkId = cpr.getDynmkId()
                if not CP.addConnectedPatientId(cpr, self.ID, self.dynmkId):
                    print(f'A redundant Patient got Connected: Name: {self.Name} ID: {self.ID} DNMKID: {self.dynmkId}')
                CP.handlePatConOpen(cpr, self) # saving the patient details anyway

    def onMessage(self, payload, isBin):        
        p = CP.getMsgParsed(payload, isBin)
        if p is None:
            p = 'Message is Invalid please check & re-send.'
            print(p)
            CP.send(self, p)
            return

        f = p['from']
        g = CP.getPart(p['msg'])
        print(f'A message from {self.Desig} {self.Name} ID: {self.ID} {f"DMNKID: {self.dynmkId}" if f == "patient" else ""} -[Part of message is: {g}...ctd]-')
        if f == 'doctor':
            CP.handleMsgFromDoctor(cpr, self, payload, p['pld'])
        elif f == 'patient':
            CP.handleMsgFromPatient(cpr, self, payload, p['pld'])
        elif f == 'dev':
            printLists()
            CP.send(self, 'dev-ack. check logs.')
        else:
            CP.send(self, 'Invalid Param -from-, please check')

    def onClose(self, wasClean, code, reason):
        print(f'Closing connection to {"-[a duplicate]-" if self.IsDuplicate else ""} {self.Desig} {self.Name} ID: {self.ID} {f"DMNKID: {self.dynmkId}" if self.Desig == "Patient" else ""} Reason: {reason}')
        if self.IsDuplicate:
            return
        if self.Desig == 'Doctor':
            CP.handleDocConClose(cpr, self)
        elif self.Desig == 'Patient':
            CP.handlePatConClose(cpr, self)

if __name__ == '__main__':

    import sys
    import time as T
    from twisted.python import log
    from twisted.internet import reactor
    cpr = CP.CPR()
    fnm = f'sslogs_{int(T.time())}.txt'
    print(f'Starting server on [ws://]localhost:9090\nAll logs will goto .\{fnm} file')
    f = open(fnm, 'w')
    log.startLogging(f)

    factory = WebSocketServerFactory("ws://127.0.0.1:9090")
    factory.protocol = MyServerProtocol
    # factory.setProtocolOptions(maxConnections=2)

    # note to self: if using putChild, the child must be bytes...

    try:
        reactor.listenTCP(9090, factory)
        reactor.run()   # this piece of code if blocking one
    except Exception as e:
        print('Exception in reactor run():', e)
    finally:
        f.close()
    
