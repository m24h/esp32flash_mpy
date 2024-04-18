import sys
import machine
from array import array
from struct import unpack

if 'esp32c3' in sys.implementation._machine.lower():
    import esp
    import esp32
    page=4096
    size=esp.flash_size()
    from esp import flash_read  as readinto
    from esp import flash_write as write
    from esp import flash_erase as erase
    # make all flash MMU mapped, for ESP32C3, there are 128 entries, each enter means 64k,
    # and virtual address is from 0x3c000000, MMU table is from 0x600C5000
    _mmu=array('L', (0,)*128)
    free=array('L')
    for i in range(128):
        t=machine.mem32[0x600C5000+(i<<2)]
        if t&0x100:
            free.append(i)
        elif not t&~0x7F:
            _mmu[t]=0x3c000000+(i<<16)
    t=0
    for i in range(size>>16):
        if not _mmu[i]:
            if t>=len(free):
                raise MemoryError('No available MMU entry')
            machine.mem32[0x600C5000+(free[t]<<2)]=i
            _mmu[i]=0x3c000000+(free[t]<<16)
            t=t+1
    def vaddr(faddr):
        return _mmu[faddr>>16]+(faddr&0xffff)
    # find a partition which has a label 'bin'
    if t:=esp32.Partition.find(type=esp32.Partition.TYPE_DATA, label='bin'):
        t=t[0].info()
        bin_addr=t[2]
        bin_size=t[3]
    else:
        bin_addr=0
        bin_size=0
    del t, i, free
else:
    raise NotImplementedError('Not a supported MCU')

def mem32(pos):
    return machine.mem32[vaddr(pos)]

def mem16(pos):
    return machine.mem16[vaddr(pos)]

def mem8(pos):
    return machine.mem8[vaddr(pos)]

class Bin:
    def __init__(self, addr, size):
        self.addr=addr
        self.size=size
    
    def mem32(self, pos):
        return machine.mem32[vaddr(pos+self.addr)]
    
    def mem16(self, pos):
        return machine.mem16[vaddr(pos+self.addr)]
    
    def mem8(self, pos):
        return machine.mem8[vaddr(pos+self.addr)]
    
    def readinto(self, offset, barray):
        readinto(offset+self.addr, barray)
    
    # encoded label must be no longer than 8 bytes
    def findsub(self, label):
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
