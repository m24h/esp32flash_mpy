# run in micropython, or `mpremote run <this script>`
__import__('vfs').VfsFat.mkfs(__import__('flashbdev').bdev)