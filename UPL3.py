# UPL3.py - uniapt I/O module
# last modified 28Oct2018 0800

global WORD1, GREG, UCOR, GRB, GR, ADR1, ADR1P, UEXIT 

# subroutine functions in support of 07 opcodes ==============
# d7 = {1:WORD1, 2: GREG, 3: UCOR, 4: GRB, 5: UGRB, 6: LINK, 7: link, 8: ADR1, 9: ADR1P, 10: UEXIT, 11: ERRFLG, 12: ERR}

#    disk io basics
#     a = 0x44444444
#     aa = a.to_bytes(4,byteorder='big')
#     f = open('up7.bin','wb')
#    f.write(aa)
#    f.write(aa)
#    f.close()
#    f = open('up7.bin','rb')
#    f.seek(4)    # position at byre 4
#    aaa = f.read(4)
#    aaaa = int.from_bytes(aaa,byteorder='big')
#    hex(aaaa) 
#    0x44444444

# disk all seq =  word 1:  RL - UCBA
#                 word 2:  disk addr

RFLAG = 0
RWBFLG = 0 
FN7 = 0
DA = 0
RL = 0
FN = 0
UCBA = 0
buff = []
DBA = 0
DBAP = 0
RWBCF = 0 
WPS = 8 
EXTFLG = 0 
SSA = 0 
RWBN = 0 
ICL = 0 
MWHDA = 0 

print('initializing RWB')
RWB = [0x22222222,] * 8

# open up7.bin as f11
f11 = open('up7.bin','r+b') 

def cumadr(d7): 
	er = 0
	WORD1 = d7[1]
	GRB = d7[4]
	GREG = d7[2]
	UCOR = d7[3]
	
	addr = WORD1 & 0xfff
	if addr < 0o20:
		if (GRB + addr) > 31: return 
		ADR1 = GRB + addr
		ADR1P = GREG 
	else:
		ADR1 = addr
		ADR1P = UCOR 
	d7[8] = ADR1
	d7[9] = ADR1P 
	return er
	
def dskcs1(d7):
	global DA, RL, UCBA, FN7, FN 
	ADR1 = d7[8]
	ADR1P = d7[9]
	RL = (ADR1P[ADR1] >> 16) & 0xfff
	UCBA = ADR1P[ADR1] & 0xfff 
	DA = ADR1P[ADR1+1] 
	DA = ((DA >> 4) & 0x7fff000) + (DA & 0xfff) 
	return 
	
def dskcsq(d7):
	global DA, RL, UCBA, FN7, FN, EXTFLG 
	EXTFLG = 0
	dskcs1(d7)
	FN = (DA >> 12) & 0o7 
	if FN == 7: FN7 = 1
	else:       FN7 = 0
	DA = ((DA >> 6) & 0o7770000) + (DA & 0o7777) 
	return
	
def getfn(da):
	global f99, f11, foff 
	foff = da 
	er = 0
	f99 = f11 
	return er
	
def dskrdr(): 
	global foff, RWBN, WPS, RWBCF 
	dadr = RWBN * WPS 
	er = getfn(dadr)
	if er: return er
	f99.seek(foff * 4) 
	xx = 0
	while xx < WPS:
		f99data = f99.read(4)
		f99datax = int.from_bytes(f99data, byteorder='big')
		RWB[xx] = f99datax
		xx += 1
	RWBCF = 0
	return
	
def dskwtr(): 
	global foff, RWBN, WPS, RWBCF 
	dadr = RWBN * WPS 
	er = getfn(dadr)
	if er: return er
	f99.seek(foff * 4) 
	xx = 0
	while xx < WPS:
		f99datax = RWB[xx]
		f99data = f99datax.to_bytes(4,byteorder='big')
		f99.write(f99data)
		xx += 1
	RWBCF = 0
	
def rwbchk():
	global RWBCF 
	er = 0 
	if RWBCF == 0: return er 
	er = dskwtr() 
	return er 
	
def rwbch():
	global RWBCF 
	er = 0
	RWBCF = 1 
	if EXTFLG == 0:
		er = dskwtr()
		return er 
	
def dsklok():
	global DA, EXTFLG, SSA, EDA, ICL, WPS, RWBFLG, RWBN, DBA, DBAP, AL 
	EDA = DA
	if EXTFLG == 0: EDA = EDA + SSA      # scratch 
	X = EDA - SSA 
	if (X >= 0) and (X < ICL * WPS):     # ICB 
		DBA = X 
		DBAP = ICB 
		AL = ICL * WPS - X 
		RWBFLG = 0 
		return 
	X = int(EDA / WPS) 
	RX = EDA % WPS 
	EDA = MWHDA + SSA 
	Y = int(EDA / WPS)
	RY = EDA % WPS 
	if (X == Y) and (RX < RY):            # WFB 
		DBA = RX 
		DBAP = WFB 
		AL = RY - RX 
		RWBFLG = 0
		return 
	if X == RWBN:                         # RWB 
		DBA = RX
		DBAP = RWB 
		AL = WPS - RX 
		RWBFLG = 1 
		return 
	else: 
		rwbchk() 
		RWBN = X 
		if (RFLAG != 0) or (RX != 0) or (RL < WPS):   # init rwb buffer 
			dskrdr() 
			
		DBA = RX
		DBAP = RWB 
		AL = WPS - RX 
		RWBFLG = 1 
		return 
	
def dskiot(d7):
	global DA, UCBA, RL, AL, RWBFLG,DBA, DBAP, RFLAG, FN7 
	UCOR = d7[3] 
	if (UCBA + RL) > 0o10000: return 0o10 
	er = getfn(DA)
	if er: return 0o11
	while RL > 0:
		dsklok()
		if (AL > RL): AL = RL
		RL = RL - AL 
		if RFLAG:
			ix = 0
			while ix < AL:
				UCOR[UCBA + ix] = DBAP[DBA + ix]
				ix += 1
		else:
			ix = 0
			while ix < AL:
				DBAP[DBA + ix] = UCOR[UCBA + ix]
				ix += 1
		UCBA += AL
		DA += AL 
		if ((RFLAG == 0) and RWBFLG == 1):
			rwbch()
	return 
	
# input/output routines for opcode 07 ========================
def case0700(d7):    # DOBTR 
	pass
def case0701(d7):     # DOBTF 
	pass
def case0702(d7):    # DOBTL 
	pass
def case0703(d7):    # DOBTN 
	pass
def case0704(d7):    # DCLOS 
	pass
def case0705(d7):    # DCLAL 
	pass 
def case0706(d7):    # DRDF 
	pass 
def case0707(d7):    # DWRF 
	pass 
def case0710(d7):    # DRDFA 
	pass 
def case0711(d7):    # DWRA 
	global FN7, RFLAG 
	dskcsq(d7)
	FN7 = 0
	RFLAG = 0
	er = dskiot(d7)
	return
	
def case0712(d7):    # DRDA 
	global FN7, RFLAG 
	dskcsq(d7)
	FN7 = 0
	RFLAG = 1
	er = dskiot(d7)
	return
	
def case0713(d7):    # TTOUT
	pass
def case0714(d7):    # CDIN 
	pass 
def case0715(d7):    # TTECO
	pass
def case0716(d7):    # CDINC 
	pass
def case0717(d7):    # OBLNG 
	pass
def case0720(d7):    # CDINN 
	pass 
def case0721(d7):    # TYPEC 
	pass 
def case0722(d7):    # PTOUT 
	pass 
def case0723(d7):    # PTIN 
	pass 
def case0724(d7):    # PTINN 
	pass
def case0725(d7):    # PTINC 
	pass 
def case0726(d7):    # DRSWR 
	pass 
def case0727(d7):    # DRSRD 
	pass 
def case0730(d7):    # DWRFA 
	pass 
def case0731(d7):    # DRSRA 
	pass 
def case0732(d7):    # PROUT 
	pass 
def case0733(d7):    # E03
	er = 3; return
def case0734(d7):    # PPAGE
	ppage = 1; return
def case0735(d7):   # DRSWA 
	pass 
def case0737(d7):      # SGR
	WORD1 = d7[1]
	n = WORD1 & 0x777
	if n > 31: er = 7; return
	d7[4] = n   # GRB 
	d7[5] = n    # UGRB 
	return

def case0740(d7):     # CSL   clear link
	link = d7[7]
	if link !=0:  link -= 1
	print('new link = ', oct(link))
	d7[7] = link 
	return
	
def case0741(d7):      # CSLX      clear saved links
	link = d7[7]
	link = 0
	print('link = ',oct(link))
	d7[7] = link 
	return 

def case0742(d7):     # DRDAX 
	pass 
def case0743(d7):     # DWRAX 
	pass 
def case0744(d7):     # XIU 
	pass 	
def case0745(d7):     # XUI 
	pass 
def case0746(d7):      # XUDS
	pass 
	
def case0747(d7):      # EXIT 
	UEXIT = d7[10]
	print('UEXIT - end')
	UEXIT = 1
	d7[10] = UEXIT
	return
		
def case0750(d7):      # CMU
	er = cumadr(d7)
	if er: return
	ADR1 = d7[8]
	ADR1P = d7[9]
	data = ADR1P[ADR1]
	ADR1P[ADR1] = ((data << 4) & 0xffff0000) + (data & 0xfff)
	return 
		
def case0751(d7):      # CUM
	er = cumadr(d7)
	if er: return
	ADR1 = d7[8]
	ADR1P = d7[9]
	data = ADR1P[ADR1] 
	ADR1P[ADR1] = ((data >> 4) & 0xffff000) + (data & 0xfff)
	return 
def case0752(d7):   # CIF 
	pass 
def case0753(d7):   # COF 
	pass 
def case0754(d7):
	pass
	
def case0777(d7):      # E03 invalid opcode
	print('invalid 07 opcode')
	er = 3; return
	
# processing for 07 routines =================================

def uplio(d7):                              # general I/O
	WORD1 = d7[1] 
	sopc = (WORD1 >> 16) & 0o77
	er = 0
	
	sw07 = {
		0: case0700, 1: case0701, 2: case0702, 3: case0703, 4: case0704, 5: case0705, 6: case0706, 7: case0707,
		0o10: case0710, 0o11: case0711, 0o12: case0712, 0o13: case0713, 0o14: case0714, 0o15: case0715,
		0o21: case0721, 0o26: case0726, 0o27: case0727, 
		0o30: case0730, 0o31: case0731, 0o32: case0732, 0o33: case0733, 0o34: case0734, 0o37: case0737, 
		0o40: case0740, 0o41: case0741, 0o42: case0742, 0o43: case0743, 0o44: case0744, 0o45: case0745, 0o46: case0746, 0o47: case0747,
		0o50: case0750, 0o51: case0751, 0o54: case0754
		}
		
	sw07.get(sopc, case0777)(d7)    # execute the function err = 77
	if er: 
		ERRFLG = 1;  ERR = er; er = 1 
		d7[11] = ERRFLG 
		d7[12] = ERR 
	return er 
	
