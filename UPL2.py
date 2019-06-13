# UPL2.py  - float package 

"""
	This routine supports the original 12 bit 2's compl exponent and 36 bit 2's compl mantissa
	The 12/36 bit format is converted to native Python float for processing then converted back to 12/36 
	The routines include float arith, integer arith (24 bit) and 3-D vector operations
"""

global UCOR, GREG
import math 

def pflt(addr, addrp):    # convert UPL float to python float
	
	udata1 = addrp[addr]
	udata2 = addrp[addr + 1]
	
	if (udata1 == 0) and (udata2 == 0): return float(0)
	uexp = udata1 >> 16 
	uman = ((udata1 & 0xfff) << 24) + ((udata2 >> 4) & 0xfff000) + (udata2 & 0xfff)
	hexsign = '+'
	if udata1 & 0x800:    # negative?
		hexsign = '-'
		uman = (~uman & 0xfffffffff) + 1
	expsign = uexp & 0o4000
	if expsign:  uexp = (~uexp & 0xfff) + 1 # flip exponent if neg
	if expsign:
		hexexp = '-'
	else:
		hexexp = '+'
	umanhex = hex(uman)
	if umanhex[:1] == '-': umanhex = umanhex[3:]
	else:  umanhex = umanhex[2:]
	flthex = hexsign + '0x0.' + umanhex + 'p' + hexexp + str(uexp)
	newflt = float.fromhex(flthex)
	print ('float = ',newflt)
	return newflt
	
def ufput(data, addr, addrp):   # store python float in UCOR or GR addr
	print ('float result = ',data)
	if data == 0.0:
		udata1 = 0x00000000
		udata2 = 0x00000000
	else:
		flthex = float.hex(data)  # convert float to hex string  '-0xH.HHHHHH-E'
		ix = flthex.index('0x')
		flthex = flthex[ix+2] + flthex[ix+4:]   # hex without the decimal
		ix = flthex.index('p')
		fltexp = int(flthex[ix+1:]) + 4
		flthex = flthex[:10]  # isolate hex digits only 10
		fltval = int(flthex,16)
		while fltval & 0x4000000000 == 0:  # normalize mantissa to second bit
			fltval = fltval << 1
			fltexp -= 1
		fltval = fltval >> 4   # keep only 9 hex digits
		if data < 0:         # neg? 
			fltval = (~fltval & 0xfffffffff) + 1
		flthex = hex(fltval)
		flthex = flthex[2:]  # strip off 0x
		flthex =flthex[:9]   # truncate to 9 hex digits
		fltval = int(flthex,16)
		if fltexp < 0:  # neg exponent, flip exponent
			fltexp = (~fltexp & 0xfff) + 1
		udata1 = (fltexp << 16) + ((fltval >> 24) & 0xfff)
		udata2 = ((fltval & 0xfff000) << 4) + (fltval & 0xfff)
		
	addrp[addr] = udata1
	addrp[addr+1] = udata2 
	return 
	
# float math routines

def ufad(greg1, addr, addrp, greg2, GREG):   # float add
	ufput(pflt(greg1, GREG) + pflt(addr, addrp), greg2, GREG) 
	return
	
def ufsb(greg1, addr, addrp, greg2, GREG):   # float sub
	ufput(pflt(greg1, GREG) - pflt(addr, addrp), greg2, GREG) 
	return
	
def ufmpy(greg1, addr, addrp, greg2, GREG):   # float mpy
	ufput(pflt(greg1, GREG) * pflt(addr, addrp), greg2, GREG)
	return
	
def ufdiv(greg1, addr, addrp, greg2, GREG):   # float divide
	ufput(pflt(greg1, GREG) / pflt(addr, addrp), greg2, GREG) 
	return
	
def ufsqrt(addr, addrp, greg2, GREG):   # float sqrt
	ufput(math.sqrt(pflt(addr, addrp)), greg2, GREG)              
	
def ufsqar(addr, addrp, greg2, GREG):   # float square
	fval = pflt(addr, addrp)
	ufput(fval * fval, greg2, GREG)                              
	
def ufcomp(addr, addrp, greg2, GREG):   # float compare
	fval1 = pflt(addr, addrp)
	fval2 = pflt(greg2, GREG)
	if fval1 < fval2:  fcomp = -1
	elif fval1 > fval2:  fcomp = 1
	else: fcomp = 0
	return fcomp
	
def ufneg(addr, addrp, greg2, GREG):    #  float neg
	fval = pflt(addr, addrp)
	ufput (-fval, greg2, GREG)
	
def ufabs(addr, addrp, greg2, GREG):    # float abs
	fval = pflt(addr, addrp)
	ufput(abs(fval), greg2, GREG)
	
# ===================== immediate int routines

def ufint(addr, addrp, greg2, GREG):    # float to int?
	fval = pflt(addr, addrp)
	ufput(int(fval), greg2, GREG)
	
def uflif(data, greg2, GREG):    # load immed float
	flt = float(data)
	ufput(flt, greg2, GREG) 
	
def ufaif(data, greg2, GREG):     # add immed float
	flt = float(data)
	ufput(flt + pflt(greg2, GREG), greg2, GREG)
	
def ufmif(data, greg2, GREG):     # mult immed float
	flt = float(data)
	ufput(flt * pflt(greg2, GREG), greg2, GREG)
	
def ufdif(data, greg2, GREG):     # div immed float
	flt = float(data) 
	ufput(pflt(greg2, GREG) / flt, greg2, GREG)
	
	
# vector routines ==============================================

def ufvmag(addr, addrp, greg, GREG):    # vmag routine 
	flt1 = pflt(addr, addrp)
	flt2 = pflt(addr+2, addrp)
	flt3 = pflt(addr+4, addrp)
	ufput(math.sqrt(flt1*flt1 + flt2*flt2 + flt3*flt3), greg, GREG)
	
def ufvnorm(addr, addrp, greg, GREG):    # vnorm 
	flt1 = pflt(addr, addrp)
	flt2 = pflt(addr+2, addrp)
	flt3 = pflt(addr+4, addrp)
	flt = math.sqrt(flt1*flt1 + flt2*flt2 + flt3*flt3)
	ufput(flt1 / flt, addr, addrp)
	ufput(flt2 / flt, addr+2, addrp)
	ufput(flt3 / flt, addr+4, addrp)
	ufput(flt, greg, GREG)      # finally store vmag 
	
def ufvadd(addr1, addr2, addr3, addr1p, addr2p, addr3p):
	flt1 = pflt(addr1, addr1p) + pflt(addr2, addr2p)
	flt2 = pflt(addr1+2, addr1p) + pflt(addr2+2, addr2p)
	flt3 = pflt(addr1+4, addr1p) + pflt(addr2+4, addr2p)
	store3(flt1, flt2, flt3, addr3, addr3p)

def ufvsub(addr1, addr2, addr3, addr1p, addr2p, addr3p):
	flt1 = pflt(addr1, addr1p) - pflt(addr2, addr2p)
	flt2 = pflt(addr1+2, addr1p) - pflt(addr2+2, addr2p)
	flt3 = pflt(addr1+4, addr1p) - pflt(addr2+4, addr2p)
	store3(flt1, flt2, flt3, addr3, addr3p)
	
def ufvdot(addr1, addr2, addr3, addr1p, addr2p, addr3p):
	flt1 = pflt(addr1, addr1p) * pflt(addr2, addr2p)
	flt2 = pflt(addr1+2, addr1p) * pflt(addr2+2, addr2p)
	flt3 = pflt(addr1+4, addr1p) * pflt(addr2+4, addr2p)
	ufput(flt1 + flt2 + flt3, addr3, addr3p)

def ufvcrx(addr1, addr2, addr3, addr1p, addr2p, addr3p):
	flt1 = pflt(addr1+2, addr1p) * pflt(addr2+4, addr2p) - pflt(addr1+4, addr1p) * pflt(addr2+2, addr2p)
	flt2 = pflt(addr2, addr2p) * pflt(addr1+4, addr1p) - pflt(addr1, addr1p) * pflt(addr2+4, addr2p)
	flt3 = pflt(addr1, addr1p) * pflt(addr2+2, addr2p) - pflt(addr2, addr2p) * pflt(addr1+2, addr1p)
	store3(flt1, flt2, flt3, addr3, addr3p)
	
def ufvsmpy(addr1, addr2, addr3, addr1p, addr2p, addr3p):
	flt = pflt(addr2, addr2p)
	flt1 = pflt(addr1, addr1p) * flt
	flt2 = pflt(addr1+2, addr1p) * flt 
	flt3 = pflt(addr1+4, addr1p) * flt 
	store3(flt1, flt2, flt3, addr3, addr3p)
	
def store3(flt1, flt2, flt3, addr, addrp):
	ufput(flt1, addr, addrp)
	ufput(flt2, addr+2, addrp)
	ufput(flt3, addr+4, addrp)
	
