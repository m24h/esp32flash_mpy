# esp32flash_mpy
A module to access flash memory directly using MMU, with partition tools and file packing/unpacking tools

## flash.py

It is impossible to access flash memory by using machine.memXX function, because the memory mapping is not fixed and linear in ESP32. 

So if you have a lot of const data which is needed to be accessed, you have to choose file system and access it in block device mode. That is so inefficient and slow for random access needs.

This module will modify the memory mapping table when it is imported and provide the translation between virtual address and physical flash memory address. You can read the right memory using its memXX() function. It is very useful for such works like doing binary search on big size data.

This module also provides class and function to access different flash data block on a divided data partition. Following script will help you to change partition on ESP32, and to pack files together for downloading.

This module currently support ESP32C3 only, but it is easy to support other ESP32 chips by modifying some parameters inside the module. The parameters include MMU table address, number of entries, start virtual address, etc.

Install:
```bash
mpremote mip install github:m24h/esp32flash_mpy
```

Examples:
```python
import flash
a=flash.mem32(0x10)
# if there's a data partition named 'bin' (the name is fixed in module's code)
b=flash.bin.mem32(34)
file1=flash.bin.findsub('eng5X8')
c=file1.mem32(10)
d=file1.findsubn('some')
```

## How to make a partition devided

It is needed to devide a partition from micropython's VFS file system, to store data continuously and not affected by the file system.

The first thing to do is changing partition table before first time running micropython after it is downloaded to the board. Or micropython will automatically format the file system on its first time running, but the partition table will be changed at future. 

So, after downloading micropython, do not reset the system, but use esptool.py (pip install esptool) to get the old partion table, which located at address 0x8000, with length 0xc00.

```sh
python -m esptool -p <port> read_flash 0x8000 0xc00 par.bin
```

Convert it to CSV format by provided script par_bin2csv.py .
```sh
python par_bin2csv.py par.bin > par.csv
```
In fact, you can get the old partition table from micropython .bin firmware directly, skip last steps, just do this.
```sh
python par_bin2csv.py firmware.bin 0x8000 > par.csv
```
You can modify the CSV file, to change the size of last data partition, and to add a new data partition, like this.
```
data, nvs, 0x9000, 0x6000, nvs, 
data, phy, 0xf000, 0x1000, phy_init, 
app, factory, 0x10000, 0x1f0000, factory, 
data, fat, 0x200000, 0x100000, vfs, 
data, undefined, 0x300000, 0x100000, bin, 
```
Then convert the CSV file back to binary format.
```sh
python par_csv2bin.py par.csv par.bin
```
And download it to ESP32 board.
```sh
python -m esptool -p <port> write_flash 0x8000 par.bin
```
Reset the board, micropython will use the first partition with label 'vfs', and you can treat the sencond partition as a big RODATA segment.

## How to packing data files
You may need to packing several files together, for downloading to the devided partition and accessing their data at run time.

The script bin_pack.py can pack files together, in the format specified by class flash.Bin. You can access file data by the file name, but for the sake of economy, the name can only be 8 bytes long.

```sh
python bin_pack.py partition.bin mydata1 mydata2 mydata3
```
Use esptool to download partition data to ESP32 board. In my example, the partition for containing my data is from address 0x300000.
```sh
python -m esptool -p <port> write_flash 0x300000 partition.bin
```
Then, you can use the class bin for accessing you data.
```python
mydata1=flash.bin.findsub('mydata1')
mydata2=flash.bin.findsub('mydata2')
```
A script bin_unpack.py is also provided for unpacking files from partition data made by bin_pack.py.
