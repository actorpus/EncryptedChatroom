"""
STILL EXPERIMENTAL
use with SecurityV2 compatible server
"""

import pygame
import win32con
import win32gui
import threading
import math
import SecurityV2


def connect_client(self, *args, **kwargs):  # for simulating login delay
    self.connection = SecurityV2.SecureSocketWrapper.Client((self.login_boxes[0], int(self.login_boxes[1])))

    self.connection.send(
        {
            "type": 2,  # authentication
            "uuid": self.login_boxes[2],
            "pass": self.login_boxes[3]
        }
    )

    while True:
        try:
            data = self.connection.receive(1024)
        except EOFError:
            continue

        lock.acquire()
        renderer.chat.append(data["uuid"] + " > " + data["content"])
        lock.release()


def wndProc(oldWndProc, draw_callback, hWnd, message, wParam, lParam):
    if message == win32con.WM_SIZE:
        draw_callback()
        win32gui.RedrawWindow(hWnd, None, None, win32con.RDW_INVALIDATE | win32con.RDW_ERASE)

    return win32gui.CallWindowProc(oldWndProc, hWnd, message, wParam, lParam)


class main:
    def __init__(self):
        pygame.init()

        self.display = pygame.display.set_mode((400, 400), pygame.RESIZABLE | pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 30)
        self.detail_font = pygame.font.SysFont(pygame.font.get_default_font(), 15)

        self.entry_box = ""
        self.chat = []
        self.screen = 0
        self.login_boxes = ["", "3953", "", ""]
        self.uuid = None
        self.login_box_select = 0
        self.login_boxes_precompute = [
            self.font.render("IP:", True, 0xA1ADFF),
            self.font.render("PORT:", True, 0xA1ADFF),
            self.font.render("UUID:", True, 0xA1ADFF),
            self.font.render("PASSWORD:", True, 0xA1ADFF),
            130 - self.font.render("IP:", True, 0xA1ADFF).get_width(),
            130 - self.font.render("PORT:", True, 0xA1ADFF).get_width(),
            130 - self.font.render("UUID:", True, 0xA1ADFF).get_width(),
            130 - self.font.render("PASSWORD:", True, 0xA1ADFF).get_width()
        ]

        self.loading = 0

        self.connection = None

    def draw(self):
        if self.screen == 0:
            self.draw_login()

        elif self.screen == 1:
            self.draw_loading()

        elif self.screen == 2:
            self.draw_main()

    def draw_loading(self):
        w, h = self.display.get_size()

        self.display.fill(0x36393F)

        self.display.blit(self.font.render("Awaiting secure connection.", True, 0xA1ADFF), (5, 5))

        for _ in range(7):
            pygame.draw.circle(
                self.display,
                0xA1ADFF,
                (
                    math.sin(self.loading + (math.pi / 3.5) * _) * 15 + w // 2,
                    math.cos(self.loading + (math.pi / 3.5) * _) * 15 + h // 2
                ),
                4 + (_ * (self.loading / 10)) / 5
            )

        self.loading += 0.2

        if self.loading > math.pi * 2:
            self.loading = 0

        if self.connection is not None:
            self.screen = 2

        pygame.display.update()

    def draw_main(self):
        w, h = self.display.get_size()

        # background
        self.display.fill(0x36393F)

        # background detail (dark grey boxes)
        pygame.draw.rect(self.display, 0x282B30, (5, 5, w - 120, h - 40), border_radius=4)
        pygame.draw.rect(self.display, 0x282B30, (w - 110, 5, 105, h - 40), border_radius=4)
        pygame.draw.rect(self.display, 0x282B30, (5, h - 30, w - 10, 25), border_radius=4)

        # current message box
        self.display.blit(self.font.render(self.entry_box, True, 0xAFB1B3), (10, h - 27))

        # chat history
        for i, msg in enumerate(self.chat[-((h - 60) // 20):]):
            self.display.blit(self.font.render(msg, True, 0xAFB1B3), (10, i * 20 + 7.5))

        # information
        self.display.blit(self.detail_font.render("CONNECTION INFO:", True, 0xA1ADFF), (w - 105, 10))
        self.display.blit(self.detail_font.render("IP: %s" % self.login_boxes[0], True, 0x828385), (w - 105, 24))
        self.display.blit(self.detail_font.render("PORT: %s" % self.login_boxes[1], True, 0x828385), (w - 105, 40))
        self.display.blit(self.detail_font.render("UUID: %s" % self.login_boxes[2], True, 0x828385), (w - 105, 55))

        pygame.display.update()

    def draw_login(self):
        w, h = self.display.get_size()

        self.display.fill(0x36393F)

        pygame.draw.rect(self.display, 0xA1ADFF, (4, 9 + (self.login_box_select * 40), w - 8, 32), border_radius=4)

        for _ in range(4):
            pygame.draw.rect(self.display, 0x313131, (5, 10 + (_ * 40), 145, 30), border_radius=4)
            pygame.draw.rect(self.display, 0x282B30, (140, 10 + (_ * 40), w - 145, 30), border_radius=4)

            self.display.blit(self.login_boxes_precompute[_], (self.login_boxes_precompute[_ + 4], 16 + (_ * 40)))

            if _ != 3:  # protected input
                self.display.blit(self.font.render(self.login_boxes[_], True, 0xAFB1B3), (145, 16 + (_ * 40)))
            else:
                self.display.blit(self.font.render("*" * len(self.login_boxes[3]), True, 0xAFB1B3), (145, 16 + (_ * 40)))

        pygame.display.update()

    def run(self):
        oldWndProc = win32gui.SetWindowLong(
            win32gui.GetForegroundWindow(),
            win32con.GWL_WNDPROC,
            lambda *args: wndProc(oldWndProc, self.draw, *args)
        )

        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return

                elif e.type == pygame.VIDEORESIZE:
                    new_w = e.w if e.w >= 200 else 200
                    new_h = e.h if e.h >= 150 else 200

                    pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE | pygame.DOUBLEBUF)

                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_UP:
                        if self.login_box_select > 0:
                            self.login_box_select -= 1

                    elif e.key == pygame.K_DOWN:
                        if self.login_box_select < 3:
                            self.login_box_select += 1

                    key = e.unicode

                    if key == "\x08":
                        if self.screen == 0:
                            self.login_boxes[self.login_box_select] = self.login_boxes[self.login_box_select][:-1]
                        elif self.screen == 2:
                            self.entry_box = self.entry_box[:-1]

                    elif key == "\r" or key == "\t":  # enter or tab
                        if self.screen == 0:
                            self.login_box_select += 1

                            if self.login_box_select == 4:
                                self.screen = 1
                                _ = threading.Thread(target=connect_client, args=(self,))
                                _.daemon = True
                                _.start()

                        elif self.screen == 2 and key == "\r" and self.entry_box:
                            self.connection.send(
                                {
                                    "type": 1,  # message
                                    "content": self.entry_box,
                                    "uuid": self.uuid
                                }
                            )
                            self.entry_box = ""

                    else:
                        if self.screen == 0:
                            self.login_boxes[self.login_box_select] += key
                        elif self.screen == 2:
                            self.entry_box += key

            self.draw()
            self.clock.tick(30)

if __name__ == '__main__':
    lock = threading.Lock()

    renderer = main()
    renderer.run()
