import json
from threading import Timer
import base64 as b64

class CPR():
	def __init__(self):
		print('cpr init')
		self.DYNMK_ID = -1
		self.pids = {}
		self.CurPatientForDoctor = {}
		self.lConnectedPatients = {}
		# self.lConnectedPatientsForDoctor = {}
		self.ReddntPatients = {}
		self.lDoctorWSConnections = set()
		self.lConnectedDids = set()
		self.lPatientWSConnections = set()

	def getDynmkId(self):
		self.DYNMK_ID += 1
		return  self.DYNMK_ID


def updateCurrPidList(O, idList, did):
	O.pids[did] = idList
	return

def getandRemoveCurPidList(O, did):
	t = O.pids[did]
	O.pids.pop(did, 'No Such Key')
	return t

def removeFromCurPidList(O, did):
	print(f'Removing doctor did: {did} from pids List.')
	if did in O.pids:
		O.pids.pop(did, 'No Such Key')

def addConnectedDoctorId(O, id):
	if id in O.lConnectedDids:
		#forceDisconnectDoctorWSConnection(O, id) # not defined yet!!
		return False
	O.lConnectedDids.add(id)
	print('addConnectedDoctorId:', O.lConnectedDids)
	return True

def removeConnectedDoctorId(O, did):
	print(f'Removing doctor did: {did} from ConnectedDoctorId List.')
	if did in O.lConnectedDids:
		O.lConnectedDids.discard(did)

def addConnectedPatientId(O, pid, dmid):
	t = O.lConnectedPatients
	if pid not in t:
		t[pid] = {dmid} # assign new set with one element dmid
		return True
	elif dmid in t[pid]:
		return False
	t[pid].add(dmid)
	lConnectedPatients = t
	return True
		
def removeConnectedPatientId(O, pid, dmid):
	print(f'Removing patient pid: {pid} dmnkid: {dmid} from ConnectedPatientId List.')
	if pid in O.lConnectedPatients:
		O.lConnectedPatients[pid].discard(dmid)
		if len(O.lConnectedPatients[pid]) == 0:
			O.lConnectedPatients.pop(pid, 'No such key')
			
def addCurrPidForCurDid(O, did, pid):
	t = O.CurPatientForDoctor
	if did in t and t[did] == pid:
		return False
	t[did] = pid
	O.CurPatientForDoctor = t
	return True
		
def removeCurrPidForCurDid(O, did):
	O = O.CurPatientForDoctor.pop(did, 'key not found')
	print(f'Removing currpid for did: {did} from CurrPatientForDoctor List. Result: {O}')
	return
		
def getCurrPidForCurDid(O, did):
	t = O.CurPatientForDoctor
	if did in t:
		return t[did]
	return None
		
def addDoctorWSConnection(O, ctx):
	t = O.lDoctorWSConnections
	for x in t:
		if x.ID == ctx.ID:
			return False
	t.add(ctx)
	O.lDoctorWSConnections = t
	return True
		
def removeDoctorWSConnection(O, did):
	print(f'Removing doctor did: {did} from WSConnection List.')
	t = O.lDoctorWSConnections.copy()
	for x in t:
		if x.ID == did:
			O.lDoctorWSConnections.discard(x)
				
def addPatientWSConnection(O, ctx):
	addRedundantPatient(O, ctx.ID, ctx.dynmkId) # not defined yet!!
	O.lPatientWSConnections.add(ctx)
		
def removePatientWSConnection(O, pid, dynmkid):
	print(f'Removing patient pid: {pid} dmnkid: {dynmkid} from WSConnection List.')
	t = O.lPatientWSConnections.copy()
	for x in t:
		if x.ID == pid and x.dynmkId == dynmkid:
			O.lPatientWSConnections.discard(x)
			return True
	return False
		
def addRedundantPatient(O, pid, dynmkid):
	t = O.ReddntPatients
	if pid in t:
		t[pid].add(dynmkid)
	else:
		t[pid] = {dynmkid}
	O.ReddntPatients = t
		
def removeRedundantPatient(O, pid, dynmkid):
	print(f'Removing patient pid: {pid} dmnkid: {dynmkid} from Redundant List.')
	if pid in O.ReddntPatients:
		O.ReddntPatients[pid].discard(dynmkid)
		if len(O.ReddntPatients[pid]) == 0:
			O.ReddntPatients.pop(pid, 'No Such Key')
			
def getRedundantPatient(O, pid):
	t = O.ReddntPatients
	return t.get(pid, set())
		
def removePatient(O, pid, dynmkid):
	removePatientWSConnection(O, pid, dynmkid)
	removeRedundantPatient(O, pid, dynmkid)
	removeConnectedPatientId(O, pid, dynmkid)
		
def removeDoctor(O, did):
	removeDoctorWSConnection(O, did)
	removeConnectedDoctorId(O, did)
	removeCurrPidForCurDid(O, did)
	removeFromCurPidList(O, did)
		
def disconnectAllPatientsXcept(O, dynmkid, did, pid):
	d = j2s({'from': 'server', 'for': 'patient', 'type': 'wrapup_and_disconnect'})
	dyids = getRedundantPatient(O, pid)
	dyids.discard(dynmkid)
	t = O.lPatientWSConnections
	for x in t:
		if x.dynmkId in dyids:
			send(x, d)
			Timer(1.0, closeCon, [x]).start()
				
def notifyConnectedPatientsAbtCurDoc(O, did, name, pids, typ):
	d = {
		'from': 'server', 
		'for': 'patient', 
		'type': typ if typ is not None else 'doctor_available', 
		'msg': f'{did}:{name}:{"online" if typ is None else "offline"}'
	}
	d = j2s(d)
	t = O.lPatientWSConnections
	for x in t:
		if x.ID in pids:
			send(x, d)
				
def notifyDoctorAboutPatient(O, pid, dmid, typ):
	d = j2s({'from': 'server', 'for': 'doctor', 'type': typ, 'pid': pid})
	if len(getRedundantPatient(O, pid)) > 1:
		return
	t = O.lDoctorWSConnections
	for x in t:
		if pid in x.PidList:
			send(x, d)
				
def notifyCurDocAbtConnectedPatients(O, x, pids):
	d = {'from': 'server', 'for': 'doctor', 'type': 'patient_available'}
	for p in pids:
		if patientIsInConnectedList(O, p):
			d['pid'] = p
			send(x, j2s(d))
			
def patientIsInConnectedList(O, pid):
	t = O.lConnectedPatients
	return pid in t and len(t[pid]) > 0;
		
def sendFromDoctorToPatient(O, msg, did, pid):
	if pid is None:
		pid = getCurrPidForCurDid(O, did)
	t = O.lPatientWSConnections
	for x in t:
		if x.ID == pid:
			send(x, msg)
				
def sendFromPatientToDoctor(O, msg, did):
	t = O.lDoctorWSConnections
	for x in t:
		if x.ID == did:
			send(x, msg)
			break
				
def forceDisconnectDoctorWSConnection(O, did):
	d = j2s({'from': 'server', 'for': 'doctor', 'type': 'safe_disconnect', 'msg': 'You are being disconnected'})
	t = O.lDoctorWSConnections
	for x in t:
		if x.ID == did:
			send(x, d)
			closeCon(x, 'You were not responding')
			break

def getDocConDetails(O, did):
	t = O.lDoctorWSConnections
	for x in t:
		if x.ID == did:
			return x
	return None

def handleDocConOpen(O, ctx):
	pids = getPidList(ctx)
	id = ctx.ID
	nm = ctx.Name
	updateCurrPidList(O, pids, ctx.ID)
	addDoctorWSConnection(O, ctx)
	showBanner(ctx)
	notifyCurDocAbtConnectedPatients(O, ctx, pids)
	notifyConnectedPatientsAbtCurDoc(O, id, nm, pids, None)

def handleDocConClose(O, ctx):
	ctx.IsConnected = False
	notifyConnectedPatientsAbtCurDoc(O, ctx.ID, ctx.Name, getPidList(ctx), 'doctor_disconnected')
	removeDoctor(O, ctx.ID)
        
def handlePatConOpen(O, ctx):
	id = ctx.ID
	dmid = ctx.dynmkId
	print('dmid:', dmid)
	showBanner(ctx)
	addPatientWSConnection(O, ctx)
	addConnectedPatientId(O, id, dmid)
	notifyDoctorAboutPatient(O, id, dmid, "patient_available")

def handlePatConClose(O, ctx):
	notifyDoctorAboutPatient(O, ctx.ID, ctx.dynmkId, "patient_disconnected")
	removePatient(O, ctx.ID, ctx.dynmkId)

def handleMsgFromPatient(O, ctx, rawMsg, p):
	try:
		#pid = p['pid']
		did = str(p['did'])
		t = p['type']
		print('A Message from Patient type: {0}'.format(t))
		if t == 'answer':
			disconnectAllPatientsXcept(O, ctx.dynmkId, did, ctx.ID)
		sendFromPatientToDoctor(O, rawMsg, did)
	except Exception as e:
		print('Exception:', e)

def handleMsgFromDoctor(O, ctx, rawMsg, p):
	d = {'from': 'server', 'for': 'doctor'}
	try:
		t = p['type']
		print('A Message from Doctor type: {0}'.format(t))
		if t == 'update_curr_pid':
			d['type'] = 'ack_pid_updtd'
			act = p['action']
			did = ctx.ID
			if act == 'add':
				pid = p['pid']
				if not addCurrPidForCurDid(O, did, pid):
					d['msg'] = f'pid {0} for did: {1} is Already Added'.format(pid, did)
				else:
					d['msg'] = f'pid {0} for did: {1} Added'.format(pid, did)
			elif act == 'remove':
				removeCurrPidForCurDid(O, did)
			send(ctx, j2s(d))
		elif t =='notification':
			pid = p['uid']
			sendFromDoctorToPatient(O, rawMsg, None, pid)
		elif t == 'update_list':
			pids = p['pids']
			updatePidList_doctor(ctx, pids)
			notifyCurDocAbtConnectedPatients(O, ctx, pids)
			d['type'] = 'ack'
			d['msg'] = 'List Updated Successfully'
			send(ctx, j2s(d))
		else:
			sendFromDoctorToPatient(O, rawMsg, ctx.ID, None)

	except Exception as e:
		print('Exception in handleMsgFromDoctor:', e)
    	
def showBanner(x):
	d = j2s({'from': 'server', 'type': 'ack', 'msg': 'Welcome to pyCBSS. Enjoy the service.'})
	send(x, d)

def addPidList_doctor(ctx, p):
    ctx.PidList = p

def updatePidList_doctor(ctx, p):
    ctx.PidList.update(p)

def getPidList(ctx):
    return ctx.PidList

def getParams(p):
	ex = False
	target = None
	token = None
	mParams = None
	typ = None
	id = None
	name = None
	frm = None
	desig = None
	pids = set()
	try:
		target = p['target'][0]
		if target == 'main':
			token = b2s(p['queuni'][0])
			checkToken(token)
			mParams = b2j(p['id'][0])
			frm = mParams['from']
			 
			if frm == 'doctor':
				id = mParams['did']
				name = mParams['docName']
				desig = 'Doctor'
				pids = set(mParams['pids'])
				p = {'typ': 'm', 'from': frm, 'desig': desig, 'name': name, 'id': id, 'pids': pids}
			elif frm == 'patient':
				id = mParams['pid']
				name = mParams['patName']
				desig = 'Patient'
				p = {'typ': 'm', 'from': frm, 'desig': desig, 'name': name, 'id': id}
			else:
				ex = True
		elif target == 'test':
			p = {'typ': 't'}
		else:
			ex = True
	except Exception as e:
		print('Handling run-time error:', e)
		ex = True

	if ex:
		return None
	 
	return p 

def getMsgParsed(pld, isBin):
	s = pld.decode('utf8')
	pld = s2j(s)
	try:
		pld = { 'pld': pld, 'from': pld['from'], 'msg': s}
	except Exception as e:
		pld = None
	return pld

def closeCon(x, y=None):
	print('peer to be closed:', x.peer)
	c = None if y is None else 1000
	try:
		x.sendClose(c, y)
		print('Connection Closed.')
	except e:
		print('Error closing connection')
		pass

def send(x, m, isBin=False):
	ii = isinstance(m, str) # if false --> bytes
	p = f'-[Part of message is: {getPart(m)}...ctd]-' if ii else '-[From onMessage]-'
	print(f'Sending message to {x.Desig} {x.Name} ID: {x.ID} {f"DMNKID: {x.dynmkId}" if x.Desig == "Patient" else ""} {p}')
	m = m.encode('utf8') if ii else m
	x.sendMessage(m, isBin)

def checkToken(t):
	pass

def b2s(b):
	return b64.b64decode(b.encode('utf8')).decode('utf8')

def b2j(b):
	return s2j(b2s(b))

def j2s(j):
	try:
		j = json.dumps(j)
	except Exception as e:
		print('Exception:', e)
		j = None
	return j

def s2j(s):
	try:
		s = json.loads(s)
	except Exception as e:
		print('Exception:', e)
		s = None
	return s

def getPart(s, mx=40):
	l = len(s)
	l = l if l <= mx else mx
	return s[0:l]

def printLens(O):
	print(f'{"-=-" * 10}Lengths{"-=-" * 10}')
	print('DYNMK_ID:', O.DYNMK_ID)
	print('pids:', len(O.pids))
	print('CurPatientForDoctor:', len(O.CurPatientForDoctor))
	print('lConnectedPatients:', len(O.lConnectedPatients))
	print('ReddntPatients:', len(O.ReddntPatients))
	print('lDoctorWSConnections:', len(O.lDoctorWSConnections))
	print('lConnectedDids:', len(O.lConnectedDids))
	print('lPatientWSConnections:', len(O.lPatientWSConnections))

def printAll(O):
	print(f'{"-=-" * 10}Values{"-=-" * 10}')
	print('DYNMK_ID:', O.DYNMK_ID)
	print('pids:', O.pids)
	print('CurPatientForDoctor:', O.CurPatientForDoctor)
	print('lConnectedPatients:', O.lConnectedPatients)
	print('ReddntPatients:', O.ReddntPatients)
	print('lConnectedDids:', O.lConnectedDids)
	d = {}
	w = O.lDoctorWSConnections
	for t in w:
		d['did'] = t.ID
	print('lDoctorWSConnections:', d)
	d = {}
	w = O.lPatientWSConnections
	for t in w:
		d['pid:dmnkid'] = f'{t.ID} : {t.dynmkId}'
	print('lPatientWSConnections:', d)
