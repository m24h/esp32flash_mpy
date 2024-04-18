import sys
import os
from struct import unpack

if len(sys.argv)<2:
	print (f'''\
Unpack files from a binaray data, which is the raw ESP32 partition by my flash.py module.
This script will extract all files to current directory.
Usage: 
	python {sys.argv[0]} <packed filename>
''')
	exit(1)

idx=0
flen=os.stat(sys.argv[1]).st_size
with open(sys.argv[1], 'rb') as f:
	while idx+16<=flen:
		f.seek(idx)
		addr, size, name=unpack('<LL8s', f.read(16))
		idx=idx+16
		if addr==0xFFFFFFFF or addr==0:
			break
		name=name.strip(b' \0\xFF').decode('utf-8')
		with open(name, 'wb') as save:
			f.seek(addr)
			save.write(f.read(size))
