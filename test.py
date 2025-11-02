import pygame
import sys
import win32gui
import win32con
import win32api

# 初始化 Pygame
pygame.init()

# 设置窗口
width, height = 300, 300
screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
pygame.display.set_caption("顶层半透明圆")

# 获取窗口句柄
hwnd = pygame.display.get_wm_info()["window"]

# 设置窗口样式为分层窗口（支持透明度）
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                       win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) |
                       win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST)

# 设置窗口透明度（0-255，0完全透明，255不透明）
win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 180, win32con.LWA_ALPHA)

# 设置窗口位置
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 100, 100, width, height, 0)

# 主循环
clock = pygame.time.Clock()
running = True
dragging = False
drag_start = (0, 0)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                dragging = True
                drag_start = event.pos
            elif event.button == 3:  # 右键
                running = False

    # 处理窗口拖动
    if dragging:
        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            dx = pos[0] - drag_start[0]
            dy = pos[1] - drag_start[1]
            current_pos = win32gui.GetWindowRect(hwnd)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST,
                                  current_pos[0] + dx, current_pos[1] + dy,
                                  width, height, 0)
        else:
            dragging = False

    # 绘制
    screen.fill((0, 0, 0, 0))  # 透明背景

    # 绘制半透明圆
    pygame.draw.circle(screen, (255, 100, 100, 180), (width // 2, height // 2), 100)
    pygame.draw.circle(screen, (255, 0, 0, 255), (width // 2, height // 2), 100, 2)

    # 显示提示文字
    font = pygame.font.SysFont('Arial', 12)
    text = font.render('拖拽移动 右键关闭', True, (255, 255, 255))
    screen.blit(text, (width // 2 - text.get_width() // 2, height // 2 - 6))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()