import logging
import typing as t
from random import randint

import pygame

from .constants import COLUMNS, CROSS, INIT_LOC_CONSTANT, ROWS
from .display import Display
from .keypad import Keypad
from .memory import Memory
from .opcode import Opcode

pygame.mixer.init()

__all__ = ("CPU",)


class CPU:
    """
    CPU of the Emulator.
    """

    __slots__ = (
        "DT",
        "I",
        "PC",
        "ST",
        "V",
        "display",
        "halt",
        "keypad",
        "memory",
        "op",
        "sound",
        "stack",
    )

    def __init__(self, display: Display, memory: Memory, keypad: Keypad) -> None:
        """
        CPU construtor.

        Args:
            memory: Primary Memory of size 4096 bytes.
            display: Display Handler for rendering sprites.
            keypad: 16-key hexadecimal keypad for taking input.

        Attributes:
            sound (pygame.mixer.Sound): A [pygame.mixer.Sound](https://www.pygame.org/docs/ref/mixer.html#pygame.mixer.Sound) object.
            op (Opcode): Opcode for identifying operation.

            V (List[int]): 16 General Purpose 8-bit registers.
            I (int): 16-bit Index register to store memory locations.
            DT (int): 8-bit Delay Timer.
            ST (int): 8-bit Sound Timer.
            PC (int): 16-bit register to store the currently executing address.
            stack (List[int]): Array of 16 16-bit values for nesting subroutines.

            halt (bool): Flag to check if the CPU is halted.
        """
        # devices
        self.display = display
        self.memory = memory
        self.keypad = keypad
        self.sound: pygame.mixer.Sound = pygame.mixer.Sound("beep.mp3")
        self.op: Opcode = Opcode(inst=0x0000)

        # registers
        self.V: t.List[int] = [0] * 16
        self.I: int = 0
        self.DT: int = 0
        self.ST: int = 0
        self.PC: int = INIT_LOC_CONSTANT
        self.stack: t.List[int] = [0] * 16

        # flags
        self.halt: bool = False

    def SYS_addr(self) -> None:
        """
        $0nnn - Jump to a machine code routine at nnn. (Edit: use kk instead)
        """
        optab = {0xE0: self.CLS, 0xEE: self.RET}
        optab[self.op.kk]()

    def CLS(self) -> None:
        """
        $00E0 - Clear the display.
        """
        self.display.clear()

    def RET(self) -> None:
        """
        $00EE - Return from a subroutine.
        """
        self.PC = self.stack.pop()

    def JP_addr(self) -> None:
        """
        $1nnn - Jump to location nnn. (PC = nnn)
        """
        self.PC = self.op.nnn

    def CALL_addr(self) -> None:
        """
        $2nnn - Call subroutine at nnn.
        """
        self.stack.append(self.PC)
        self.PC = self.op.nnn

    def SE_Vx_byte(self) -> None:
        """
        $3xkk - Skip next instruction if Vx = kk.
        """
        if self.V[self.op.x] == self.op.kk:
            self.PC += 2

    def SNE_Vx_byte(self) -> None:
        """
        $4xkk - Skip next instruction if Vx != kk.
        """
        if self.V[self.op.x] != self.op.kk:
            self.PC += 2

    def SE_Vx_Vy(self) -> None:
        """
        $5xy0 - Skip next instruction if Vx = Vy.
        """
        if self.V[self.op.x] == self.V[self.op.y]:
            self.PC += 2

    def LD_Vx_byte(self) -> None:
        """
        $6xkk - Set Vx = kk.
        """
        self.V[self.op.x] = self.op.kk

    def ADD_Vx_byte(self) -> None:
        """
        $7xkk - Set Vx = Vx + kk.
        """
        self.V[self.op.x] = (self.V[self.op.x] + self.op.kk) & 0xFF

    def JP_addr_8(self) -> None:
        """
        $8xyn -  Jump to a machine code routine at n.
        """
        optab = {
            0x0: self.LD_Vx_Vy,
            0x1: self.OR_Vx_Vy,
            0x2: self.AND_Vx_Vy,
            0x3: self.XOR_Vx_Vy,
            0x4: self.ADD_Vx_Vy,
            0x5: self.SUB_Vx_Vy,
            0x6: self.SHR_Vx_Vy,
            0x7: self.SUBN_Vx_Vy,
            0xE: self.SHL_Vx_Vy,
        }
        optab[self.op.n]()

    def LD_Vx_Vy(self) -> None:
        """
        $8xy0 - Set Vx = Vy.
        """
        self.V[self.op.x] = (self.V[self.op.y]) & 0xFF

    def OR_Vx_Vy(self) -> None:
        """
        $8xy1 - Set Vx = Vx OR Vy.
        """
        self.V[self.op.x] = (self.V[self.op.x] | self.V[self.op.y]) & 0xFF
        self.V[0xF] = 0

    def AND_Vx_Vy(self) -> None:
        """
        $8xy2 - Set Vx = Vx AND Vy.
        """
        self.V[self.op.x] = (self.V[self.op.x] & self.V[self.op.y]) & 0xFF
        self.V[0xF] = 0

    def XOR_Vx_Vy(self) -> None:
        """
        $8xy3 - Set Vx = Vx XOR Vy.
        """
        self.V[self.op.x] = (self.V[self.op.x] ^ self.V[self.op.y]) & 0xFF
        self.V[0xF] = 0

    def ADD_Vx_Vy(self) -> None:
        """
        $8xy4 - Set Vx = Vx + Vy, set VF = carry.
        """
        val = self.V[self.op.x] + self.V[self.op.y]
        self.V[self.op.x] = val & 0xFF

        if val > 0xFF:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0

    def SUB_Vx_Vy(self) -> None:
        """
        $8xy5 - Set Vx = Vx - Vy, set VF = NOT borrow.
        """
        x = self.V[self.op.x]
        y = self.V[self.op.y]

        self.V[self.op.x] = (x - y) & 0xFF

        if x < y:
            self.V[0xF] = 0
        else:
            self.V[0xF] = 1

    def SHR_Vx_Vy(self) -> None:
        """
        $8xy6 - Set Vx = Vx SHR 1.
        """
        prev = self.V[self.op.x]
        self.V[self.op.x] = self.V[self.op.y]
        self.V[self.op.x] = (self.V[self.op.x] >> 1) & 0xFF
        self.V[0xF] = prev & 1

    def SUBN_Vx_Vy(self) -> None:
        """
        $8xy7 - Set Vx = Vy - Vx, set VF = NOT borrow.
        """
        self.V[self.op.x] = (self.V[self.op.y] - self.V[self.op.x]) & 0xFF
        if self.V[self.op.x] > self.V[self.op.y]:
            self.V[0xF] = 0
        else:
            self.V[0xF] = 1

    def SHL_Vx_Vy(self) -> None:
        """
        $8xyE - Set Vx = Vx SHL 1.
        """
        y = self.V[self.op.y]

        self.V[self.op.x] = (y << 1) & 0xFF
        self.V[0xF] = (y & 0xFF) >> 7

    def SNE_Vx_Vy(self) -> None:
        """
        $9xy0 - Skip next instruction if Vx != Vy.
        """
        if self.V[self.op.x] != self.V[self.op.y]:
            self.PC += 2

    def LD_I_addr(self) -> None:
        """
        $Annn - Set I = nnn.
        """
        self.I = self.op.nnn

    def JP_V0_addr(self) -> None:
        """
        $Bnnn - Jump to location nnn + V0.
        """
        self.PC = self.op.nnn + self.V[0]

    def RND_Vx_byte(self) -> None:
        """
        $Cxkk - Set Vx = random byte AND kk.
        """
        self.V[self.op.x] = randint(0, 0xFF) & self.op.kk

    def DRW_Vx_Vy_nibble(self) -> None:
        """
        $Dxyn - Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision. :)
        """
        x = self.V[self.op.x] % COLUMNS
        y = self.V[self.op.y] % ROWS

        self.V[0xF] = 0

        for i in range(self.op.n):
            sprite = self.memory.space[self.I + i]
            if (y + i) <= ROWS:
                for j in range(8):
                    if (x + j) <= COLUMNS:
                        px = (sprite >> (7 - j)) & 1
                        index = self.display.wrap(x + j, y + i)

                        if px == 1 and self.display.buffer[index] == 1:
                            self.V[0xF] = 1

                        self.display.buffer[index] ^= px

    def Jp_addr_E(self) -> None:
        """
        $Exkk - Jump to a machine code routine at kk.
        """
        optab = {0x9E: self.SKP_Vx, 0xA1: self.SKNP_Vx}
        optab[self.op.kk]()

    def SKP_Vx(self) -> None:
        """
        $Ex9E - Skip next instruction if key with the value of Vx is pressed.
        """
        if self.keypad.state[self.V[self.op.x] & 0xF]:
            self.PC += 2

    def SKNP_Vx(self) -> None:
        """
        $ExA1 - Skip next instruction if key with the value of Vx is not pressed.
        """
        if not self.keypad.state[self.V[self.op.x] & 0xF]:
            self.PC += 2

    def Jp_addr_F(self) -> None:
        """
        $Fxkk - Jump to a machine code routine at kk.
        """
        optab = {
            0x07: self.LD_Vx_DT,
            0x0A: self.LD_Vx_K,
            0x15: self.LD_DT_Vx,
            0x18: self.LD_ST_Vx,
            0x1E: self.ADD_I_Vx,
            0x29: self.LD_F_Vx,
            0x33: self.LD_B_Vx,
            0x55: self.LD_I_Vx,
            0x65: self.LD_Vx_I,
        }
        optab[self.op.kk]()

    def LD_Vx_DT(self) -> None:
        """
        $Fx07 - Set Vx = delay timer value.
        """
        self.V[self.op.x] = self.DT

    def LD_Vx_K(self) -> None:
        """
        $Fx0A - Wait for a key press, store the value of the key in Vx.
        """
        event = pygame.event.wait()
        if event.type == pygame.KEYUP:
            if event.key in self.keypad.keymap:
                key = self.keypad.keymap[event.key]
                self.V[self.op.x] = key
                self.keypad.unset(key)

            if event.type == pygame.QUIT:
                self.display.destroy()
        else:
            self.PC -= 2

    def LD_DT_Vx(self) -> None:
        """
        $Fx15 - Set delay timer = Vx.
        """
        self.DT = self.V[self.op.x]

    def LD_ST_Vx(self) -> None:
        """
        $Fx18 - Set sound timer = Vx.
        """
        self.ST = self.V[self.op.x]

    def ADD_I_Vx(self) -> None:
        """
        $Fx1E - Set I = I + Vx.
        """
        self.I += self.V[self.op.x]

    def LD_F_Vx(self) -> None:
        """
        $Fx29 - Set I = location of sprite for digit Vx.
        """
        self.I = (self.V[self.op.x] * 5) & 0x0FFF

    def LD_B_Vx(self) -> None:
        """
        $Fx33 - Store BCD representation of Vx in memory locations I, I+1, and I+2.
        """
        self.memory.space[self.I] = self.V[self.op.x] // 100
        self.memory.space[self.I + 1] = (self.V[self.op.x] % 100) // 10
        self.memory.space[self.I + 2] = self.V[self.op.x] % 10

    def LD_I_Vx(self) -> None:
        """
        $Fx55 - Store registers V0 through Vx in memory starting at location I.
        """
        for i in range(self.op.x + 1):
            self.memory.space[self.I + i] = self.V[i]
        self.I += self.op.x + 1

    def LD_Vx_I(self) -> None:
        """
        $Fx65 - Read registers V0 through Vx from memory starting at location I.
        """
        for i in range(self.op.x + 1):
            self.V[i] = self.memory.space[self.I + i]
        self.I += self.op.x + 1

    @property
    def optable(self) -> t.Mapping[int, t.Callable[..., None]]:
        """
        Opcode function lookup table.

        Returns:
            dict: opcode.type:subroutine mapping.
        """
        return {
            0x0: self.SYS_addr,
            0x1: self.JP_addr,
            0x2: self.CALL_addr,
            0x3: self.SE_Vx_byte,
            0x4: self.SNE_Vx_byte,
            0x5: self.SE_Vx_Vy,
            0x6: self.LD_Vx_byte,
            0x7: self.ADD_Vx_byte,
            0x8: self.JP_addr_8,
            0x9: self.SNE_Vx_Vy,
            0xA: self.LD_I_addr,
            0xB: self.JP_V0_addr,
            0xC: self.RND_Vx_byte,
            0xD: self.DRW_Vx_Vy_nibble,
            0xE: self.Jp_addr_E,
            0xF: self.Jp_addr_F,
        }

    def beep(self) -> None:
        """
        Make a beep sound.
        """
        self.sound.play()

    def cycle(self) -> None:
        """
        Fetch, Decode and Execute instructions from the memory.
        Also, decrease timers.
        """
        fetch = (self.memory.space[self.PC] << 8) | self.memory.space[self.PC + 1]
        self.op = Opcode(fetch)
        self.PC += 2

        try:
            self.optable[(self.op.type & 0xF000) >> 12]()
        except KeyError:
            logging.error(f"{CROSS} Opcode not found: {hex(self.op.type)}")
            self.display.destroy()

        self.handle_timers()

    def handle_timers(self) -> None:
        """
        Decrement ST and DT.
        """
        if self.DT > 0:
            self.DT -= 1

        if self.ST > 0:
            self.ST = 0
            self.beep()
