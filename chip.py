import math
import random
import time
import logging

#setup the debugger printing function
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug")

def debug_print(fmt, *args):
    logger.debug(fmt, *args)
    
# Memory Map:
    
#     Total = 4096 Bytes
# Opcodes are Big-endian

#Fontset
fontset = bytearray([
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80   # F
])

memory = bytearray(4096)

#Registers, 16 GP 8 bit registers start with V and then havea  Hex code
V = bytearray(16)
# index register and program counter
I = 0
#pc starts at memory location 0x200 since the prevous 512bytes are for the interperter 
pc = 0x200 
#stack pointer
sp = 0
#stack is an array of 16 16bit values
stack = bytearray(16)
#keypad is hex, I probably could assign the keys here but will do that in the main.py with the pygame keybaord controls.
keypad = bytearray(16)
#display 64x32 pixels. I'll need a way to scale this 
display = bytearray(64 * 32)
#Delay timer
dt = 0
#sound timer
st = 0

draw_flag = 0
sound_flag = 0

def init_cpu():
    random.seed(int(time.time()))
    
    #loads the font into "memory"
    global memory, fontset
    memory[:len(fontset)] = fontset[:]
    
def load_rom(filename):
    try:
        with open(filename, "rb") as fp:
            fp.seek(0x200)
            memory[0x200:] = fp.read()
    except FileNotFoundError:
        return -2
    except Exception as e:
        print(e)
        return -1
    else:
        return 0

# /**
#  * emulate_cycle: run chip-8 instructions
#  * @param void
#  * @return void
#  *
#  * 1) Fetch the operation code
#  *      - fetch one opcode from the memory at the location specified by the
#  * program counter. Each array address contains one byte, an opcode is 2 bytes
#  * long so we need to fetch 2 consecutive bytes and merge them to get the actual
#  * opcode.
#  *          - for example:
#  *              0xA2F0 --> pc = 0xA2, pc + 1 = 0xF0
#  *              opcode = pc << 8 | pc + 1
#  *                  - shifting A0 left by 8 bits, which adds 8 zeros (0xA200)
#  *                  - bitwise OR to merge them
#  *
#  * 2) Decode the operation code
#  *      - look up to the optable to see what the op means
#  *          - for example:
#  *              0xA2F0 --> ANNN: sets I to the address NNN (0x2F0)
#  * 3) Execute the operation code
#  *      - execute the parsed op
#  *          - for example:
#  *              0xA2F0 --> store 0x2F0 into the I register, as only 12-bits are
#  * containing the value we need to store, we use a bitwise AND (with the value
#  * 0x0FFF) to get rid of the first four bits.
#  *                  - I =  opcode & 0x0FFF
#  *                    pc += 2 --> every instruction is 2 bytes long
#  * 4) Update timers
#  *      - count to zero at 60hz if they are set to a number greater than 0
#  * */

def emulate_cycle():
    draw_flag = 0
    sound_flag = 0
    op = memory[pc] << 8 | memory[pc + 1]