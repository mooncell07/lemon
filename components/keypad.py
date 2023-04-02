import typing as t

import pygame as pg
from pygame.event import Event

__all__ = ("Keypad",)


class Keypad:
    """
    An object represeting a 16-key keypad of a standard keypad.
    """

    __slots__ = ("state",)

    def __init__(self) -> None:
        """
        Keypad Constructor.

        Attributes:
            state: State storing KEYUP and KEYDOWN status of the 16 keys.
        """
        self.state: t.List[int] = [0] * 16

    @property
    def keymap(self) -> t.Mapping[int, int]:
        """
        Mapping of pygame keys with locations on the keypad.
        """
        return {
            pg.K_1: 1,
            pg.K_2: 2,
            pg.K_3: 3,
            pg.K_4: 12,
            pg.K_q: 4,
            pg.K_w: 5,
            pg.K_e: 6,
            pg.K_r: 13,
            pg.K_a: 7,
            pg.K_s: 8,
            pg.K_d: 9,
            pg.K_f: 14,
            pg.K_z: 10,
            pg.K_x: 0,
            pg.K_c: 11,
            pg.K_v: 15,
        }

    def set(self, index: int) -> None:
        """
        Method to set a key in state array.

        Args:
            index: The key to set.
        """
        self.state[index] = 1

    def unset(self, index: int) -> None:
        """
        Method to unset a key in state array.

        Args:
            index: The key to unset.
        """
        self.state[index] = 0

    def handle(self, event: Event, screenshot: t.Callable[..., None]) -> None:
        """
        Handler for KEYDOWN and PRINTSCREEN.

        Args:
            event: A pygame Event.
            screenshot: Screenshot Callback.
        """
        if event.key in self.keymap:
            key = self.keymap[event.key]
            self.set(key)
            return key

        if event.key == pg.K_PRINTSCREEN:
            screenshot()
