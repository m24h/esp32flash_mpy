import sys
from hashlib import md5
from struct import pack

if len(sys.argv)<3:
	print (f'''\
Create binary parition table from .csv file. 
Usage:
	python {sys.argv[0]} <.csv filename> <.bin filename>
''')
	exit(1)

types={
	'app':0,
	'data':1
}
subtypes={
	0:{
		'factory':0,
		'test':0x20,
	},
	1:{
		'ota':0,
		'phy':1,
		'nvs':2,
		'coredump':3,
		'nvs_keys':4,
		'efuse':5,
		'undefined':6,
		'esphttpd':0x80,
		'fat':0x81,
		'spiffs':0x82,
	},
}
flags={
  'encrypted':0,
}	

bin=bytearray()
with open(sys.argv[1], 'r') as f:
	while line:=f.readline():
		line=line.strip('\r\n \t')
		if not line or line.startswith('#'):
			continue
		csv=line.strip('\r\n \t').split(',')
		bin.extend(b'\xAA\x50')
		bin.extend(pack('B', type:=types[csv[0].strip(' \t').lower()]))
		bin.extend(pack('B', subtypes[type][csv[1].strip(' \t').lower()]))
		bin.extend(pack('<L', eval(csv[2].strip(' \t'))))
		bin.extend(pack('<L', eval(csv[3].strip(' \t'))))
		bin.extend(pack('16s', csv[4].strip(' \t').encode('utf-8')))
		flag=0
		if len(csv)>5:
			for t in csv[5].split(':'):
				if t:=t.strip(' \t'):
					flag=flag+(1<<flags[t])
		bin.extend(pack('<L', flag))
bin.extend(b'\xEB\xEB'+b'\0'*14+md5(bin).digest())
bin.extend(b'\xFF'*(0xc00-len(bin)))
with open(sys.argv[2], 'wb') as f:
	f.write(bin)
