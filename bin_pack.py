import sys
from struct import pack

if len(sys.argv)<2:
	print (f'''\
Pack files into a binaray data for using raw ESP32 partition by my flash.py module.
This script will use the file name as data label, which must not be longer than 8 bytes.
Usage: 
	python {sys.argv[0]} <packed filename> [files to be packed] ...
''')
	exit(1)

addr=16*(len(sys.argv)-1)
bin=bytearray(b'\xFF'*addr)
pos=0
for fname in sys.argv[2:]:
	with open(fname, 'rb') as f:
		b=f.read()
	bin.extend(b)
	t=len(b)
	bin[pos:pos+16]=pack('<LL8s', addr, t, fname.encode('utf-8'))
	pos=pos+16
	addr=addr+t
	# align to 16 bytes
	t=(16-(addr%16))%16
	bin.extend(b'\xFF'*t)
	addr=addr+t

with open(sys.argv[1], 'wb') as f:
	f.write(bin)

