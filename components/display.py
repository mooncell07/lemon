import typing as t

import pygame

from .constants import COLORS, COLUMNS, ROWS

pygame.init()

img = pygame.image.load("./docs/img/lemon.png")
__all__ = ("Display",)


class Display:
    """
    Object for handling creation, rendering and deletion of the emulator
    window.
    """

    __slots__ = ("buffer", "multiplier", "screen")

    def __init__(self, screen: pygame.Surface, multiplier: int):
        """
        Display Constructor.

        Args:
            screen: A [pygame.Surface](https://www.pygame.org/docs/ref/surface.html#pygame.Surface) on which sprites are drawn.
            multiplier: Constant for scaling the window.

        Attributes:
            buffer (bytearray): Display Buffer; used to store sprite location on the window.
        """
        self.screen = screen
        self.multiplier = multiplier
        self.buffer: bytearray = bytearray(ROWS * COLUMNS)

    @classmethod
    def create(cls, multiplier: int) -> t.Self:
        """
        Create the window and sets caption and icon.

        Args:
            multiplier: Constant for scaling the window.

        """
        screen = pygame.display.set_mode((COLUMNS * multiplier, ROWS * multiplier))
        pygame.display.set_caption("Lemon")
        pygame.display.set_icon(img)
        self = cls(screen, multiplier)

        return self

    def refresh(self) -> None:
        """
        Refresh the display using
        [pygame.display.flip](https://www.pygame.org/docs/ref/display.html?highlight=pygame%20display%20flip#pygame.display.flip)
        """
        pygame.display.flip()

    def destroy(self) -> None:
        """
        Destroy the window and exit the emulator.
        """
        pygame.quit()
        raise SystemExit

    def wrap(self, x: int, y: int) -> int:
        """
        Wrap overflown/underflown pixels back at the opposite end.

        Args:
            x: The x position.
            y: The y position.

        Returns:
            loc: location of the cordinates in the display buffer.
        """
        x %= COLUMNS
        y %= ROWS

        loc = x + (y * COLUMNS)
        return loc

    def render(self) -> None:
        """
        Render the ON/OFF pixels onto the screen.
        """
        self.screen.fill(COLORS["OFF"])
        for i in range(ROWS * COLUMNS):
            x = (i % COLUMNS) * self.multiplier
            y = (i // COLUMNS) * self.multiplier

            if self.buffer[i]:
                pygame.draw.rect(
                    self.screen,
                    COLORS["ON"],
                    pygame.Rect(x, y, self.multiplier, self.multiplier),
                )
        self.refresh()

    def capture(self) -> None:
        """
        Screen capturing util. (Saves the output at ./out.png)
        """
        pygame.image.save(self.screen, "./out.png")

    def clear(self) -> None:
        """
        Clear the display buffer.
        """
        self.buffer = bytearray(ROWS * COLUMNS)
