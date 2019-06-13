# uniapt.py  - uniapt conversion to py from C
# last modified 30Oct2018 0800 

"""
	This interpreter was originally written for a mini computer with 12 bit words and used for numerical control processing
	It was converted to a C based system to run on 16 bit minicomputers and larger unix-based systems
		The 16 bit version stored each 12 bit word in a 16 bit word to stay compatible with the original program library
	This implementation is a Python version of the C based system
	The floating point package converts a 12 bit exponent (2-s complement) and a 36 bit mantissa (2's complement) 
		to native Python floating point 
	The trig package uses standard Python math library routines
	The disk IO package was not completed but has place holders for each routine
"""

print ('Uniapt N/C System Python Interpreter ')
print ('Creative Software Systems @ 2018. All Rights Reserved.\n')

# init data areas and constants
# LOCN array is UCORE and LOC is current location pointer


global UCOR, GREG, GR, GRB, UGRB, ADR1, ADR1P, LOC, LINK, SKIP, UEXIT 

DEBUG = 1  # disable try/except error catch

print ('initializing UCORE')
UCOR = [0x00000000,] * 4098

print ('initializing GREG')
GREG = [0x00000000,] * 32 
	
print ('initializing link stack')
LINK = [0x0000,] * 32 

# ---- build test instructions in UCOR ----- convert octal 12/12 to hex 16/16
UCOR[0o1000] = 0o00010000   # NOP
UCOR[0o1001] = 0o04211100   # CLR BIT
UCOR[0o1002] = 0o55001200   # BRA
UCOR[0o1003] = 0o00010000   # NOP
UCOR[0o1004] = 0o56001210   # BSL 1210
UCOR[0o1005] = 0o76100002   # LIF  0002 : REG 2
UCOR[0o1006] = 0o54101220   # STF  1220 : REG 2/3 
UCOR[0o1007] = 0o76100003   # LIF  0003 : reg 2/3
UCOR[0o1010] = 0o54101222   # STF
UCOR[0o1011] = 0o76100004   # LIF   0004
UCOR[0o1012] = 0o54101224   # STF
UCOR[0o1013] = 0o76100005   # LIF   0005
UCOR[0O1014] = 0o54101300   # STF 
UCOR[0o1015] = 0o76100006   # LIF   0006
UCOR[0o1016] = 0o54101302   # STF 
UCOR[0o1017] = 0o76100007   # LIF   0007
UCOR[0o1020] = 0o54101304   # STF 
UCOR[0o1021] = 0o07370004   # SGR 4    set GRB = 4
UCOR[0o1022] = 0o07370000   # SGR 0   back to  0 
UCOR[0o1023] = 0o07121030   # DRDA 1030
UCOR[0o1024] = 0o00000000 

UCOR[0o1030] = 0o00021120    # call seq    RL=2, UCBA=1120 
UCOR[0o1031] = 0o00000012   #   DA = 0o12 

UCOR[0o1100] = 0o7777
UCOR[0o1110] = 0o00033000
UCOR[0o1111] = 0o00000000

UCOR[0o1120] = 0o00010000     # LIF (for dskwrt test)
UCOR[0o1121] = 0o00010000     # STF (for disk write)

UCOR[0o1200] = 0o00010000   # NOP
UCOR[0o1201] = 0o55001003  # BRA 
UCOR[0o1210] = 0o00010000   # NOP
UCOR[0o1211] = 0o01000000   # BRR back to 1005

GREG[1] = 0o7777
GREG[2] = 0o00023000
GREG[3] = 0o00000000
GREG[4] = 0o00000000

x = 0o1000
while x < 0o1212:
	UCOR[x] = ((UCOR[x] & 0o77770000) << 4) + (UCOR[x] & 0o7777)
	x += 1
x = 1
while x < 5:
	GREG[x] = ((GREG[x] & 0o77770000) << 4) + (GREG[x] & 0o7777)
	x += 1
	
LOC = 0o1000
	
SKIP = 0
ERRFLG = 0
ERR = 0
UEXIT = 0
link = 0     # init links index
E01PEND = 0
FLAG = 0
PFLAG = 0
GRB = 0
GR = 0
UGRB = 0

from UPL2 import *      # floating point and vector routines
from UPL3 import *      # I/O module

# subroutines for setup, isolation of components

def BITAD():
	global BIT, ADR1, ADR1P, ADR1C, WORD1, GRB
	er = 0
	ibit = (WORD1 >> 18) & 0xf 
	if ibit > 11:
		ERRFLG = 1; ERR = 0o10; er = 1
		return er
	BIT = 0x800 >> ibit    # create bit
	addr = WORD1 & 0xfff   # isolate addr
	if addr < 0o20:         # test GR
		ADR1 = GRB + addr 
		ADR1P = GREG 
		if ADR1 > 31:
			ERRFLG = 1; ERR = 0o10; er = 1 
	else:
		ADR1= addr 
		ADR1P = UCOR
	return er

def GRADX0():
	global WORD1, DAT1, GREG, GRB, GR, ERRFLG, ERR , ADR1, ADR1P 
	er = 0
	DAT1 = (WORD1 >> 16) & 0o77
	addr = WORD1 & 0xfff
	if addr < 0o20:
		ADR1P = GREG 
		ADR1 = GRB + addr
		if ADR1 > 31:
			ERRFLG = 1; ERR = 0o10; er = 1
	else:
		ADR1P = UCOR 
		ADR1 = addr
	return er 

def GRADXL():
	global WORD1, GREG, GR, GRB, ADR1, ADR1P 
	er = 0
	addr = WORD1 >> 0xfff
	ix = (WORD1 >> 16) &0o3
	if ix:
		ix = GREG[GRB + ix] & 0xfff
	greg = (WORD1 >> 18) & 0xf
	XR1 = ix >> 1      # ix / 2
	XR2 = ix & 0o1     # low bit
	if addr < 0o20:
		ADR1P = GREG 
		ADR1 = GRB + addr
		if ADR1 > 31:
			ERRFLG = 1; ERR = 0o10; er = 1
	else:
		ADR1P = UCOR 
		ADR1 = addr     # UCOR
	GR = GRB + greg
	if (GRB + greg) > 31:
		ERRFLG = 1; ERR = 0o10; er = 1
	return er
	
def GRADXR():
	global WORD1, ADR1, ADR1P, GREG, GR, GRB, ERRFLG, ERR
	er = 0
	ix = (WORD1 >> 16) & 0o3
	if ix:
		ix = GREG[GRB + ix] & 0xfff    # ix contents
	greg = (WORD1 >> 18) & 0xf         # isolate gr 
	addr = (WORD1 + ix)& 0xfff
	if addr < 0o20:
		ADR1P = GREG
		ADR1 = GRB + addr
		if ADR1 > 31:
			ERRFLG = 1; ERR = 0o10; er = 1
	else:
		ADR1P = UCOR 
		ADR1 = addr
	GR = GRB + greg
	if GR > 31:
		ERRFLG = 1; ERR = 0o10; er = 1
	return er 
	
def GRDATA():
	global WORD1, ADR1, ADR1P, GRB, GR, ERRFLG, ERR
	er = 0
	greg = (WORD1 >> 18) & 0xf 
	DAT1 = WORD1 & 0xfff
	GR = GRB + greg
	if (GRB + greg) > 31: ERRFLG = 1; ERR = 0o10; er = 1
	return er 
	
def GRIMXB():   
	global WORD1, ERR, ERRFLG, GRB, GR, GREG, DAT1
	er = 0
	ix = (WORD1 >> 16) & 0o3    # index
	if ix:
		ix = GREG[GRB + ix] & 0xfff     # ix contents
	greg = (WORD1 >> 18) & 0xf         # gen reg
	DAT1 = (WORD1 + ix) & 0xfff        # data
	GR = GRB + greg
	if (GRB + greg) > 31: ERRFLG = 1; ERR = 0o10; er = 1
	return er
	
def GRIMXR():
	global GR, GREG, GRB, WORD1, DAT1, ERRFLG, ERR 
	er = 0
	ix = (WORD1 >> 16) & 0o3      # isolate index
	if ix:
		ix = GREG[GRB + ix] & 0xfff   # contents
	greg = (WORD1 >> 18) & 0xf        # isolate GR
	data = (WORD1 + ix) & 0xfff       # isolate data
	if data > 0x7ff:                  # convert 2s compl to int 
		data = ((~data) & 0xfff) + 1
		data = -data 
	DAT1 = data 
	GR = GRB + greg
	if (GRB + greg) > 31: ERRFLG = 1; ERR = 0o10; er = 1
	return er
	
def teste01():      # test pending E01
	global ERRFLG, E01PEND, ERR, FLAG, PFLAG
	if (E01PEND == 1) and ((FLAG & PFLAG) == 0):
		E01PEND = 0
		ERRFLG = 1
		if ERR == 0: ERR = 1
	return
		
# integer routines  impy idiv icomp  ===============================
	
def icomp(greg, addr, ADR1P, GREG):    # compare integers
	data1 = GREG[greg]
	data2 = ADR1P[addr]
	data1 = ((data1 << 4) & 0xfff00000) + ((data1 << 8) & 0xfff00)
	data2 = ((data2 << 4) & 0xfff00000) + ((data2 << 8) & 0xfff00)
	if data1 == data2: return 0
	if data2 < data1: return -1
	return 1
	
def impy(greg, data, GREG):    # integer multiply
	data1 = GREG[greg]
	data2 = data 
	if (data1 == 0) or (data2 == 0):  
		GREG[greg] = 0
		GREG[greg+1] = 0
		return
	sgn = signmpy(data1, data2)
	p1 = (data1 & 0xfff) * (data2 & 0xfff)      # a2 b2
	p2 = (data1 >> 12) * (data2 & 0xfff)        # a1 b2
	p3 = (data1 & 0xfff) * (data2 >> 12)        # a2 b1
	p4 = (data1 >> 12) * (data2 >> 12)          # a1 b1
	d0 = p2 + p3
	d2 = p1 + ((d0 & 0xfff) << 12)
	d1 = p4 + (d0 >> 12) + (d2 >> 24)
	if sgn:									# negate if sign
		if (d2 == 0): d1 = ~d1
		else: d2 = ~d2; d1 = ~d1
	GREG[greg] = ((d1 << 4) & 0xfff0000) + (d1 & 0xfff)
	GREG[greg+1] = ((d2 << 4) & 0xfff0000) + (d2 & 0xfff)
	
def idiv(greg, data, GREG):    # integer divide
	data1 = GREG[greg]
	data2 = data 
	if (data1 == 0) or (data2 == 0) :   
		GREG[greg] = 0
		GREG[greg+1] = 0
		return
	sgn = signmpy(data1, data2)
	d3 = data1 / data2     # quot 
	d4 = data1 % data2     # remainder
	if sgn: d3 = ((~d3) + 1) & 0xffffff    # negate quot
	GREG[greg] = ((d3 << 4) & 0xfff0000) + (d3 & 0xfff)
	GREG[greg+1] = ((d4 << 4) & 0xfff0000) + (d4 & 0xfff)
	
def signmpy(data1, data2):     # get sign of prod/quot and force pos data values 
	data = (data1 ^ data2) & 0x8000000
	if data > 0: sgn = 1
	else:        sgn = 0
	data = data1 
	data = ((data >> 4) & 0xfff000) + (data & 0xfff)
	if data > 0x7fffff: data = (~data + 1) & 0xffffff
	data1 = data
	data = data2
	data = ((data >> 4) & 0xfff000) + (data & 0xfff)
	if data > 0x7fffff: data = (~data + 1) & 0xffffff
	data2 = data 
	return sgn

# vector routines and functions ======================================

def VECTXR(): # prep for vector operations
	global WORD1, GREG, GRB, GR, UCOR, AD1, AD2, AD3, ADR1, ADR1P, LOC 
	global ADR2, ADR3, ADR2P, ADR3P 
	er = 0
	addr = WORD1 & 0xfff
	WORD2 = UCOR[LOC];  LOC += 1
	sopcd = (WORD1 >> 19) & 0o7
	
	ix = (WORD1 >> 16) & 0o3         # XR1
	if ix: ix = (GREG[GRB + ix]) & 0xfff
	addr = (addr + ix) & 0xfff
	if sopcd: 
		if addr < 0o20:
			ADR1 = GRB + addr
			ADR1P = GREG
			if ADR1 > 31: ERRFLG = 1; ERR = 0o10; er = 1
		else:
			ADR1 = addr
			ADR1P = UCOR
	else:
		ADR1 = addr
		ADR1P = UCOR
	AD1 = addr
	
	ix = (WORD1 >> 18) & 0o1          # XR2
	if ix: ix = GREG[GRB + ix] & 0xfff
	addr = WORD2 >> 16
	addr = (addr + ix) & 0xfff
	XR2 = 0
	if addr < 0o20:
		XR2 = 1
		ADR2 = GRB + addr
		ADR2P = GREG
		if ADR2 > 31: ERRFLG = 1; ERR = 0o10; er=1
	else:
		ADR2 = addr
		ADR2P = UCOR
	AD2 = addr
	addr = WORD2 & 0xfff
	if not sopcd:
		DAT3 = addr
	else:
		if addr < 0o20:
			ADR3 = GRB + addr 
			ADR3P = GREG
			if ADR3 > 31: ERRFLG = 1; ERR = 0o20; er = 1
		else:
			ADR3 = addr
			ADR3P = UCOR
	return er

# opcode processing for interpreter ====================================

def opc00():  # 00 HLT NOP
	global WORD1, ERRFLG, ERR 
	if WORD1 & 0x3f0000:
		opname = "NOP"
		return
	ERRFLG = 1; ERR = 2
	opname = "HLT"
	
def opc01():  # 01 BRR
	global LINK, link, ERRFLG, ERR, LOC 
	if link == 0:      # empty stack	
		print ('empty stack')
		ERRFLG = 1
		ERR = 6
		return
	else:
		LOC = LINK[link]
		teste01()
		link -= 1
	return
	
def opc02():  # 02 CALL CALLR
	print ('opc 02 call PL or ML')

def opc03():  # 03 LIIP BRM BRP BRN
	global WORD1, GREG, GR, DAT1, LOC 
	print ('opc 03')
	if GRDATA(): return
	sopc = (WORD1 >> 16) & 0o3
	oct3 = GREG[GR]
	def case0300():  # LIIP 
		if (oct3 & 0x800): DAT1 += 0xfff0000    # propagate sign double word
		GREG[GR] = DAT1
		return
	def case0301():  # BRM 
		if (oct3 & 0x800): LOC = DAT1
		teste01()
		return
	def case0302():  # BRP 
		if (oct3 & 0x800) == 0: LOC = DAT1
		teste01()
		return 
	def case03003():  # BRN 
		if oct3: LOC = DAT1
		teste01()
		return 
	sw03 = {0: case0300, 1: case0301, 2: case0302, 3: case0303}
	sw03.get(sopc)()
	
def opc04():  # 04 SET CLR SKN SKZ
	global ADR, ADR1, ADR1C, BIT, SKIP, UCOR, GREG, GRB
	if BITAD():	return
	print ('BIT=',oct(BIT))
	def case0400(data):   # set bit
		print ('04 SET BIT')
		data |= BIT
		return data
	def case0401(data):   # clear bit
		print('04 CLR BIT')
		data &= ~BIT 
		return data
	def case0402(data):   # skip if nonzero
		global SKIP
		print('04 SKN')
		if data & BIT: SKIP = 1
	def case0403(data):   # skip if zero
		global SKIP
		print('04 SKZ')
		if data & BIT == 0:	SKIP = 1	
	sopc = (WORD1 >> 16) & 0o3
	ADR1C = ADR1P[ADR1]
	if sopc < 2: # (set or clear)
		print ('olddata = ',oct(ADR1C))
	sw04 = {0:case0400, 1:case0401, 2:case0402, 3:case0403}
	newdata = sw04.get(sopc)(ADR1C)
	if sopc < 2:    # (set or clear)
		ADR1P[ADR1] = newdata 
		print ('newdata = ', oct(newdata))
	
def opc05():  # 05 LIB
	global LOC, WORD1, GREG, GR 
	print ('opc 05')
	LOC = WORD1 * 0xfff
	teste01()
	GREG[GRB] = (WORD1 >> 16) & 0o77 
	
def opc06():  # 06 STI
	global ADR1, ADR1P, DAT1, GREG, UCOR 
	print ('opc 06')
	if GRADX0(): return
	ADR1P[ADR1] = DAT1 
	
def opc07():  # 07 INPUT/OUTPUT
	global UEXIT, GRB, link, ERRFLG, ERR  
	if GRADX0(): return
	d7 = {1:WORD1, 2: GREG, 3: UCOR, 4: GRB, 5: UGRB, 6: LINK, 7: link, 8: ADR1,
		9: ADR1P, 10: UEXIT, 11: ERRFLG, 12: ERR}
	uplio(d7)
	GRB = d7[4]
	UEXIT = d7[10] 
	link = d7[7]
	ERRFLG = d7[11]
	ERR = d7[12] 
	
def opc10():  # 10 AMI AMIS
	global DAT1, ADR1, ADR1P, WORD1, SKIP 
	if GRADx0(): return 
	DAT3 = WORD1 & 0x200000    # sopc for AMIS 
	DAT1 = DAT1 & 0o37         # 5 bit data
	if DAT1 > 0xf: DAT1 += 0xfe0
	ADR1C = ADR1P[ADR1] 
	DAT2 = ADR1C & 0xffff0000
	DAT1 = (DAT1 + ADR1C) & 0xfff   # sum 12 bits
	ADR1P[ADR1] = DAT2 + DAT1 
	if DAT3: 
		if not DAT1: SKIP = 1     # skip if nonzero
	return 
	
def opc11():  # 11 LBC
	global ADR1P, ADR1, GREG, GR 
	if GRADXB(): return
	DAT1 = ADR1P[ADR1] 
	DAT1 =  ((DAT1 >> 4) & 0xfff000) + (DAT1 & 0xfff)
	GREG[GR] = (DAT1 >> ((3-XR2) * 6)) & 0o77 
	return 
	
def opc12():  # 12 STB
	global ADR1, ADR1P, GREG, GR 
	if GRADXB(): return
	DAT1 = 0o77 << ((3 - XR2) * 6)
	DAT2 = ADR1P[ADR1] 
	DAT2 = ((DAT2 >> 4) & 0xfff000) + (DAT2 & 0xfff)
	DAT2 = (DAT2 & (~DAT1)) + ((GREG[GR] & 0o77) << ((3 - XR2) * 6))
	ADR1C = ((DAT2 << 4) & 0xfff0000) + (DAT2 & 0xffff)
	ADR1P[ADR1] = ADR1C 
	return
	
def opc13():  # 13 BIL
	global ADR1, ADR1P, XR2, LOC 
	print ('opc BIL')
	if GRADXL(): return
	DAT1 = ADR1P[ADR1] 
	if XR2 == 0:
		DAT1 = DAT1 >> 16
	LOC = DAT1 & 0xfff
	teste01()
	return
	
def opc14():   # 14 LLW
	global ADR1, ADR1P, XR2, GREG, GR 
	if GRADXL(): return
	DAT1 = ADR1P[ADR1] 
	if XR2 == 0:
		DAT1 = DAT1 >> 16
	GREG[GR] = DAT1 & 0xffff
	return
	
def opc15():   # 15 STL
	global ADR1, ADR1P, GREG, XR2, GR 
	print ('opc STL')
	if GRADXL(): return
	if XR2 == 0:
		ADR1P[ADR1] = (ADR1P[ADR1] & 0xffff) + (GREG[GR] << 16)
	else:
		ADR1P[ADR1] = (ADR1P[ADR1] & 0xffff0000) + (GREG[GR] & 0xffff) 
	return
	
def opc16():   # 16 FAD
	if GRADXR(): return
	ufad(GR, ADR1, ADR1P, GR, GREG)
	return
	
def opc17():   # 17 FSB
	if GRADXR(): return
	ufsb(GR, ADR1, ADR1P, GR, GREG)
	return
	
def opc20():   # 20 FMP
	if GRADXR(): return
	ufmpy(GR, ADR1, ADR1P, GR, GREG)
	return
	
def opc21():   # 21 FDV
	if GRADXR(): return
	ufdiv(GR, ADR1, ADR1P, GR, GREG)
	return

def opc22():   # 22 FSU
	global SKIP
	if GRADXR(): return
	if ufcomp(ADR1, ADR1P, GR, GREG) != 0: SKIP = 1
	return 
	
def opc23():   # 23 INT
	if GRADXR(): return
	ufint(ADR1, ADR1P, GR, GREG)
	
def opc24():   # 24 NEG 
	if GRADXR(): return
	ufneg(ADR1, ADR1P, GR, GREG)

def opc25():   # 25 ABS
	if GRADXR(): return
	ufabs(ADR1, ADR1P, GR, GREG)
	
def opc26():   # 26 VMAG
	if GRADXR(): return
	ufvmag(ADR1, ADR1P, GR, GREG)
	
def opc27():   # 27 VNORM
	if GRADXR(): return
	ufvnorm(ADR1, ADR1P, GR, GREG)
	
def opc30():   # 30 SQAR
	if GRADXR(): return
	ufsqar(ADR1, ADR1P, GR, GREG)
	
def opc31():   # 31 SQRT
	if GRADXR(): return
	ufsqrt(ADR1, ADR1P, GR, GREG)
	
def opc32():   # 32 FSE
	global SKIP 
	if GRADXR(): return
	if ufcomp(ADR1, ADR1P, GR, GREG) == 0: SKIP = 1
	return 
	
def opc33():    # 33 FSG
	global SKIP
	if GRADXR(): return
	if ufcomp(ADR1, ADR1P, GR, GREG) > 0: SKIP = 1
	
def opc34():   # 34 FSS
	global SKIP
	if GRADXR(): return
	if ufcomp(ADR1, ADR1P, GR, GREG) < 0: SKIP = 1
	
def opc35():   # 35 FSL
	global SKIP
	if GRADXR(): return
	if ufcomp(ADR1, ADR1P, GR, GREG) <= 0: SKIP = 1
	
def opc36():   # 36 ADW
	global ADR1, ADR1P, GREG, GR 
	if GRADXR(): return
	ADR1C = ADR1P[ADR1] 
	DAT1 = GREG[GR] + ADR1C
	if DAT1 & 0x1000: DAT1 += 0x10000
	GREG[GR] = DAT1 &0xfff0fff
	return
	
def opc37():   # 37 SBW
	global ADR1, ADR1P, GREG, GR 
	if GRADXR(): return
	ADR1C = ADR1P[ADR1] 
	DAT1 = GREG[GR]
	DAT1 = ((DAT1 >> 4) & 0xfff000) + (DAT1 & 0xfff)
	DAT2 = ADR1C 
	DAT2 = ((DAT2 >> 4) & 0xfff000) + (DAT2 & 0xfff)
	DAT2 = ~DAT2 + 1
	DAT1 += DAT2
	GREG[GR] = ((DAT1 << 4) & 0xfff0000) + (DAT1 & 0xfff)
	return 
	
def opc40():   # 40 MWI
	if GRADXR(): return
	impy(GR, ADR1, GREG)
	
def opc41():   # 41 DWI
	if GRADXR(): return
	idiv(GR, ADR1, GREG)
	
def opc42():   # 42 LWO
	global ADR1, ADR1P, GREG, GR 
	if GRADXR(): return
	GREG[GR] = ADR1P[ADR1] 
	
def opc43():   # 43 LWF
	global ADR1, ADR1P, GREG, GR 
	if GRADXR(): return
	GREG[GR] = ADR1P[ADR1]
	GREG[GR + 1] = ADR1P[ADR1 + 1]
	
def opc44():   # 44 AND
	global ADR1, ADR1P, GREG, GR 
	if GRADXR(): return
	GREG[GR] = GREG[GR] & ADR1P[ADR1]  

def opc45():   # 45 ORD
	global ADR1, ADR1P, GREG, GR 
	if GRADXR(): return
	GREG[GR] = GREG[GR] | ADR1P[ADR1] 
	
def opc46():   # 46 CSE
	global SKIP 
	if GRADXR(): return
	if icomp(GR, ADR1, ADR1P, GREG) == 0: SKIP = 1
	
def opc47():   # 47 CSG 
	global SKIP 
	if GRADXR(): return
	if icomp(GR, ADR1, ADR1P, GREG) > 0: SKIP = 1
	
def opc50():   # 50 CSS 
	global SKIP
	if GRADXR(): return
	if icomp(GR, ADR1, ADR1P, GREG) < 0: SKIP = 1
	
def opc51():   # 51 LWC 
	if GRADXR(): return
	DAT1 = ADR1P[ADR1]
	DAT1 = ((DAT1 >> 4) & 0xfff000) + (DAT1 & 0xfff)
	DAT1 = ~DAT1 + 1
	GREG[GR] = ((DAT1 << 4) & 0xfff0000) + (DAT1 & 0xfff)

def opc52():   # 52 VMOV VADD VSUB VDOT VCRX VSMPY CJTW 
	global WORD1, ADR1, ADR2, ADR1P, ADR2P, DAT3, XR2, ERRFLG, ERR 
	sopc = (WORD1 >> 19) & 0o7
	if (sopc < 6) and VECTXR(): return
	if sopc == 7: sopc = 6         # 6 and 7 same
	def case5200():   # 0 VMOV 
		print ('52 0 VMOV')
		adt1 = ADR1 + (2 * DAT3)
		adt2 = 4096
		if adt1 > adt2: ERRFLG = 1; ERR = 0o10; return
		adt1 = ADR2 + (2 * DAT3)
		if XR2 == 1: adt2 = 32
		if adt1 > adt2: ERRFLG = 1; ERR = 0o10; return
		n = 0
		while n < DAT3:
			ADR2P[ADR2] = ADR1P[ADR1]
			ADR1 += 1; ADR2 +=1
			n += 1
	def case5201():   # 1 VADD 
		print ('52 1 VADD')
		ufvadd(ADR1, ADR2, ADR3, ADR1P, ADR2P, ADR3P)

	def case5202():   # 2 VSUB 
		print ('52 2 VSUB')
		ufvsub(ADR1, ADR2, ADR3, ADR1P, ADR2P, ADR3P)
		
	def case5203():   # 3 VDOT 
		print ('52 3 VDOT')
		ufvdot(ADR1, ADR2, ADR3, ADR1P, ADR2P, ADR3P)
		
	def case5204():   # 4 VCRX  
		print ('52 4 VCRX')
		ufvcrx(ADR1, ADR2, ADR3, ADR1P, ADR2P, ADR3P)
		
	def case5205():   # 5 VSMPY 
		print ('52 5 VSMPY') 
		ufvsmpy(ADR1, ADR2, ADR3, ADR1P, ADR2P, ADR3P)
		
	def case5206():   # 6 CJTW 
		global WORD1, GRB, GR, UCOR, LOC 
		print ('52 6 CJTW') 
		greg = (WORD1 >> 16) & 0xf
		DAT1 = WORD1 &0xffff 
		GR = GRB + greg 
		if GR > 31: ERRFLG = 1; ERR = 0o10; return 
		WORD2 = UCOR[LOC]; LOC += 1
		DAT1 = ((~DAT1) + 1 + GREG[GR]) & 0xfff
		if DAT1 > 0x7ff:
			LOC = (WORD2 >> 16) & 0xfff 
		if DAT1 == 0:
			LOC = WORD2 & 0xfff 
		teste01()
		
	def case52err():
		print ('function not defined')
		ERRFLG = 1; ERR=0o77
		
	sw52 = {0: case5200, 1: case5201, 2: case5202, 3: case5203, 
			4: case5204, 5: case5205, 6: case5206 }
	sw52.get(sopc, case52err)()
	
def opc53():   # 53 STW
	global GREG, GR, ADR1, ADR1P 
	if GRADXR(): return
	ADR1P[ADR1] = GREG[GR] 
	return

def opc54():   # 54 STF
	global GREG, GR, ADR1, ADR1P 
	if GRADXR(): return
	ADR1P[ADR1] = GREG[GR]
	ADR1P[ADR1 + 1] = GREG[GR + 1]
	
def opc55():  # 55 BRA BRZ
	global DAT1, GR, GRB, GREG, LOC
	if GRIMXB(): return
	if (GR == GRB) or (GREG[GR] == 0):
		LOC = DAT1
	teste01()
	return
	
def opc56(): # 56 BSL
	global GR, GREG, GRB, ERRFLG, ERR, LINK, link, DAT1, LOC 
	if GRIMXB(): return
	if GR == GRB:
		if link == 10: ERRFLG = 1; ERR = 6; return
		else:
			link += 1
			LINK[link] = LOC
	else:
		GREG[GR] = LOC
	LOC = DAT1
	teste01()
	return
	
def opc57():   # 57 DIB 
	global DAT1, GREG, GR, LOC 
	if GRIMXB(): return 
	DAT2 = (GREG[GR] >> 16) & 0xfff
	DAT3 = (GREG[GR] + 0xfff) & 0xfff   # decrement 
	if DAT2 != DAT3: LOC = DAT1 
	GREG[GR] = (DAT2 << 16) + DAT3 
	teste01()
	
def opc60():   # 60 IIB 
	global DAT1, GREG, GR, LOC 
	if GRIMXR(): return 
	if DAT1 <= 0: return 
	DAT2 = (GREG[GR] >> 16) & 0xfff
	DAT3 = (GREG[GR] + 1)& 0xfff        # increment 
	if DAT2 != DAT3: LOC = DAT1 
	GREG[GR] = (DAT2 << 16) + DAT3  
	
def opc61():   # 61 LSW
	global DAT1, GREG, GR 
	if GRIMXR(): return 
	if DAT1 <= 0: return
	DAT2 = GREG[GR]
	DAT2 = ((DAT2 >> 4) & 0xfff000) + (DAT2 & 0xfff)
	DAT2 = DAT2 << DAT1 
	GREG[GR] = ((DAT2 << 4) & 0xfff0000) + (DAT2 & 0xfff)
	return
	
def opc62():   # 62 RSW
	global DAT1, GREG, GR 
	if GRIMXR(): return 
	if DAT1 <= 0: return
	DAT2 = GREG[GR]
	DAT2 = ((DAT2 >> 4) & 0xfff000) + (DAT2 & 0xfff)
	DAT2 = DAT2 >> DAT1
	GREG[GR] = ((DAT2 << 4) & 0xfff0000) + (DAT2 & 0xfff)
	return
	
def opc63():   # 63 AII
	global DAT1, GREG, GR
	if GRIMXB(): return 
	if DAT1 > 0xfff: DAT1 += 0xfff0000
	DAT2 = GREG[GR] + DAT1
	if (DAT2 & 0x1000): DAT2 += 0x10000
	GREG[GR] = DAT2 & 0xfff0fff 

def opc64():   # 64 MII 
	global DAT1, GR, GREG 
	if GRIMXB(): return
	if (DAT1 > 0xfff): DAT1 += 0xfff0000 
	if DAT1 == 0: GREG[GR] = 0; GREG[GR+1] = 0; return 
	impy(GR, DAT1, GREG)
	
def opc65():   # 65 DII 
	global DAT1, GR, GREG 
	if GRIMXB(): return
	if (DAT1 > 0xfff): DAT1 += 0xfff0000 
	if DAT1 == 0: GREG[GR] = 0; GREG[GR+1] = 0; return 
	idiv(GR, DAT1, GREG)
	
def opc66():   # 66 CSI 
	global SKIP, DAT1, GREG, GR 
	if GRIMXB(): return
	if (GREG[GR] & 0xfff) != DAT1: SKIP = 1

def opc67():   # 67 CSIE 
	global SKIP, DAT1, GREG, GR 
	if GRIMXB(): return 
	if (GREG[GR] & 0xfff) == DAT1: SKIP = 1
	
def opc70():   # 70 LII 
	global DAT1, GREG, GR 
	if GRIMXB(): return
	GREG[GR] = (GREG[GR] & 0xfff0000) + DAT1 
	
def opc71():	# 71 LIS 
	global DAT1, GREG, GR 
	if GRIMXB(): return
	GREG[GR] = (DAT1 << 16) + (GREG[GR] & 0xffff)
	
def opc72():   # 72 ANI 
	if GRIMXB(): return
	DAT1 = 0xfffff000 + DAT1 
	GREG[GR] &= DAT1 
	
def opc73():   # 73 AIF
	if GRIMXR(): return
	ufaif(DAT1, GR, GREG)
	
def opc74():   # 74 MIF 
	if GRIMXR(): return
	ufmif(DAT1, GR, GREG)
	
def opc75():   # 75 DIF
	if GRIMXR(): return
	ufdif(DAT1, GR, GREG)
	
def opc76():   # 76 LIF
	if GRIMXR(): return
	uflif(DAT1, GR, GREG)
	 
def opc77():   # 77 AEI 
	if GRIMXB(): return
	GREG[GR] = ((DAT1 << 16) + GREG[GR])& 0xfffffff 
	
def opc99():
	print ('opc '+ oct(opc)[2:] + ' not found') 
	
opcodes = {
	0: opc00, 1: opc01, 2: opc02, 3: opc03, 4: opc04, 5: opc05, 6: opc06, 7: opc07,
	 0o10: opc10, 0o11: opc11, 0o12: opc12, 0o13: opc13, 0o14: opc14, 0o15: opc15, 0o16: opc16, 0o17: opc17,
	 0o20: opc20, 0o21: opc21, 0o22: opc22, 0o23: opc23, 0o24: opc24, 0o25: opc25, 0o26: opc26, 0o27: opc27,
	 0o30: opc30, 0o31: opc31, 0o32: opc32, 0o33: opc33, 0o34: opc34, 0o35: opc35, 0o36: opc36, 0o37: opc37,
	 0o40: opc40, 0o41: opc41, 0o42: opc42, 0o43: opc43, 0o44: opc44, 0o45: opc45, 0o46: opc46, 0o47: opc47,
	 0o50: opc50, 0o51: opc51, 0o52: opc52, 0o53: opc53, 0o54: opc54, 0o55: opc55, 0o56: opc56, 0o57: opc57,
	 0o60: opc60, 0o61: opc61, 0o62: opc62, 0o63: opc63, 0o64: opc64, 0o65: opc65, 0o66: opc66, 0o67: opc67,
	 0o70: opc70, 0o71: opc71, 0o72: opc72, 0o73: opc73, 0o74: opc74, 0o75: opc75, 0o76: opc76, 0o77: opc77
	}
	
# main loop thru program
while UEXIT == 0:
	if SKIP:
		print('skipping')
		WORD1 = UCOR[LOC]
		opc = (WORD1 >> 22) & 0o77
		if opc == 0o52: LOC += 1
		LOC += 1
		SKIP = 0
		if LOC > 0o7777:
			ERRFLG = 1
			ERR = 0o10
			
# get next instruction and isolate the opcode, reg, index and address

	WORD1 = UCOR[LOC]
	SAVLOC = LOC
	LOC += 1

	opc = (WORD1 >> 22) & 0o77   #   isolate op code

# simulate switch for opcode processing

	print ('%04o : %04o %04o' % (SAVLOC, WORD1>>16, WORD1 & 0o7777))
	
	if DEBUG:    # skip try/except
		opcodes.get(opc)()
	else:	
		try:
			opcodes.get(opc)()
		except KeyboardInterrupt: # keyboard interrupt - set pending E01
			E01PEND = 1
		except:
			print ('unexpected error in opcode function')
			ERRFLG = 1
			ERR = 0o77	
	if ERRFLG:     # error set
		ERRFLG = 0
		print ('%04o E%02o' % (SAVLOC, ERR))
		if ERR == 1:
			xx = input ('press <enter> to continue')
			continue
		input ('press <enter> to terminate')
		break
# end of processing
#  UEXIT exit and termination ==================================

print ('End of Uniapt Processing')

			
	
