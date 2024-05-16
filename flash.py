# NOTICE:
#   not all MCU support mem8()/mem16() method on FLASH,
#   with those MCU, data must be read in machine word using mem32(), or panic

from machine import mem32 as _mm32, mem16 as _mm16, mem8 as _mm8

size=__import__('esp').flash_size()

from esp import flash_read  as readinto
from esp import flash_write as write
from esp import flash_erase as erase

soc=__import__('sys').implementation._machine.lower()
if 'c3' in soc:
    chip='ESP32C3'
    page=4096
    # make all flash MMU mapped, for ESP32C3, there are 128 entries, each entry means 64k,
    # and virtual address is from 0x3c000000, MMU table is from 0x600C5000
    _mmu=__import__('array').array('L', (0,)*128)
    free=__import__('array').array('L')
    for i in range(128):
        t=_mm32[0x600C5000+(i<<2)]
        if t&0x100: # invalid bit
            free.append(i)
        else:
            t=t&0xFF
            if t<128: # only support 0-8M 
                _mmu[t]=0x3c000000+(i<<16)
    t=0
    for i in range(size>>16):
        if not _mmu[i]:
            if t>=len(free):
                raise MemoryError('No available MMU entry')
            _mm32[0x600C5000+(free[t]<<2)]=i
            _mmu[i]=0x3C000000+(free[t]<<16)
            t+=1
    del t, i, free
elif 's2' in soc:
    chip='ESP32S2'
    page=4096
    # make all flash MMU mapped, for ESP32S2, there are 6*64 entries, each entry means 64k,
    # we now only use first 3*64-8 IBUS entries, which's indexes are from 8 to 191
    # and virtual address is from 0x40000000 to 0x407FFFFF, MMU table is from 0x61801000
    _mmu=__import__('array').array('L', (0,)*128)
    free=__import__('array').array('L')
    for i in range(192):
        t=_mm32[0x61801000+(i<<2)]
        if t&0x4000: # invalid bit
            if i>=8:
                free.append(i)
        elif t&0x8000: # flash bit
            t=t&0x3FFF
            if t<128: # virtual address support 0-8M
                _mmu[t]=0x40000000+(i<<16)
    t=0
    for i in range(size>>16):
        if not _mmu[i]:
            if t>=len(free):
                raise MemoryError('No available MMU entry')
            _mm32[0x61801000+(free[t]<<2)]=i|0x8000 # FLASH flag
            _mmu[i]=0x40000000+(free[t]<<16)
            t+=1
    del t, i, free
else:
    raise NotImplementedError('Not a supported MCU')
del soc

def vaddr(faddr):
    return _mmu[faddr>>16]+(faddr&0xffff)

# find a partition which has a label 'bin'
import esp32
if t:=esp32.Partition.find(type=esp32.Partition.TYPE_DATA, label='bin'):
    t=t[0].info()
    bin_addr=t[2]
    bin_size=t[3]
else:
    bin_addr=0
    bin_size=0
del t, esp32

def mem32(pos):
    return _mm32[vaddr(pos)]

def mem16(pos):
    return _mm16[vaddr(pos)]

def mem8(pos):
    return _mm8[vaddr(pos)]

class Bin:
    def __init__(self, addr, size):
        self.addr=addr
        self.size=size
    
    def mem32(self, pos):
        return _mm32[vaddr(pos+self.addr)]
    
    def mem16(self, pos):
        return _mm16[vaddr(pos+self.addr)]
    
    def mem8(self, pos):
        return _mm8[vaddr(pos+self.addr)]
    
    def readinto(self, offset, barray):
        readinto(offset+self.addr, barray)
    
    # several files can be packed in to a Bin object, see bin_pack.py/bin_unpack.py
    # encoded label must be no longer than 8 bytes
    def findsub(self, label):
        from struct import unpack
        idx=0
        b=bytearray(16)
        label=label.encode('utf-8')
        while idx+16<=self.size:
            readinto(self.addr+idx, b)
            idx=idx+16
            addr, size, name=unpack('<LL8s', b)
            if addr==0xFFFFFFFF or addr==0:
                break
            if name.strip(b' \0\xFF')==label:
                return Bin(self.addr+addr, size)
        return None

bin=Bin(bin_addr, bin_size) if bin_size else None
