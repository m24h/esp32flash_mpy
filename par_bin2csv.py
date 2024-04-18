import sys
from hashlib import md5
from struct import unpack

if len(sys.argv)<2:
	print (f'''\
Read parition table from .bin file. 
For firmware .bin file, an offset of 0x8000 should be specified.
Usage:
	python {sys.argv[0]} <.bin filename> [offset, ignore means 0]
''')
	exit(1)

types={
	0:'app',
	1:'data'
}
subtypes={
	0:{
		0:'factory',
		0x20:'test',
	},
	1:{
		0:'ota',
		1:'phy',
		2:'nvs',
		3:'coredump',
		4:'nvs_keys',
		5:'efuse',
		6:'undefined',
		0x80:'esphttpd',
		0x81:'fat',
		0x82:'spiffs',
	},
}
flags={
  0:'encrypted',
}	

with open(sys.argv[1], 'rb') as f:
	offset=eval(sys.argv[2]) if len(sys.argv)>2 else 0
	f.seek(offset)
	tab=f.read(0xc00)

for i in range(0, 0xc00, 32):
	if tab[i]==0xAA and tab[i+1]==0x50: # partition entry
		type, subtype, addr, len, label, flag=unpack('<BBLL16sL', tab[i+2:i+32])
		label=label.rstrip(b'\0').decode('utf-8')
		print(f'{types[type]}, {subtypes[type][subtype]}, {addr:#x}, {len:#x}, {label}, {":".join(flags[j] for j in range(32) if flag&(1<<j))}')
	elif tab[i]==0xEB and tab[i+1]==0xEB: # md5 checksum
		if md5(tab[0:i]).digest()!=tab[i+16:i+32]:
			print('!!!BAD MD5!!!')
	elif tab[i:i+32]==b'\xFF'*32:
		break
	else:
		print('Unknown entry', tab[i:i+32])

