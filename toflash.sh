echo "Detect Chip"
esptool.py -p COM10 chip_id
echo "Erase Flash"
esptool.py --chip esp32 --port COM10 erase_flash
echo "Load Micropython"
esptool.py --chip esp32 --port COM10 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 bootloader.bin 0xf000 phy_init_data.bin 0x10000 MicroPython.bin 0x8000 partitions_mpy.bin
sleep 3
esptool.py --chip esp32 --port COM10 --after hard_reset

echo "put mpgsm.py"
ampy --port COM10 -d 5 put mpgsm.py
sleep 1
echo "put wavecom.py"
ampy --port COM10 -d 5 put wavecom.py
sleep 1
echo "put main.py"
ampy --port COM10 -d 5 put main.py
sleep 1