import pygame
import sys
import win32gui
import win32con
import win32api
import numpy as np
import ctypes
from ctypes import Structure, c_short, c_long, c_byte, c_uint, c_int, byref, c_void_p

# === Windows API 定义 ===
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32


class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


class SIZE(Structure):
    _fields_ = [("cx", c_long), ("cy", c_long)]


class BLENDFUNCTION(Structure):
    _fields_ = [("BlendOp", c_byte), ("BlendFlags", c_byte), ("SourceConstantAlpha", c_byte), ("AlphaFormat", c_byte)]


# 常量
ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01


# === 点击检测函数 ===
def is_click_on_sprite(mouse_x, mouse_y, current_frame):
    """
    检测鼠标是否点击在精灵的非透明区域上
    mouse_x, mouse_y: 鼠标在窗口内的坐标
    current_frame: 当前帧的Surface对象
    """
    # 检查是否在窗口范围内
    if 0 <= mouse_x < WIDTH and 0 <= mouse_y < HEIGHT:
        # 获取点击位置的Alpha值
        try:
            pixel_color = current_frame.get_at((mouse_x, mouse_y))
            alpha = pixel_color[3]  # Alpha通道
            return alpha > 10
        except IndexError:
            return False
    return False


# === BGRA 转换 ===
def convert_to_bgra(surface):
    rgba_data = pygame.image.tostring(surface, "RGBA")
    width, height = surface.get_size()

    arr = np.frombuffer(rgba_data, dtype=np.uint8).reshape(height, width, 4)

    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]

    # 关键：预乘 Alpha (Pre-multiplied Alpha)
    a_f = a / 255.0
    r_pre = (r * a_f).astype(np.uint8)
    g_pre = (g * a_f).astype(np.uint8)
    b_pre = (b * a_f).astype(np.uint8)

    # 重新堆叠为 BGRA 顺序
    bgra = np.dstack([b_pre, g_pre, r_pre, a])

    return bgra.tobytes()


# === 分层窗口更新 ===
def update_layered_window(hwnd, surface, window_x=None, window_y=None):
    """更新分层窗口内容"""
    width, height = surface.get_size()
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)

    class BITMAPINFO(Structure):
        _fields_ = [
            ("biSize", c_uint), ("biWidth", c_int), ("biHeight", c_int),
            ("biPlanes", c_short), ("biBitCount", c_short), ("biCompression", c_uint),
            ("biSizeImage", c_uint), ("biXPelsPerMeter", c_long), ("biYPelsPerMeter", c_long),
            ("biClrUsed", c_uint), ("biClrImportant", c_uint)
        ]

    bmi = BITMAPINFO()
    bmi.biSize = ctypes.sizeof(BITMAPINFO)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    ppv_bits = c_void_p()
    hbitmap = gdi32.CreateDIBSection(hdc_screen, byref(bmi), 0, byref(ppv_bits), None, 0)
    old_bitmap = gdi32.SelectObject(hdc_mem, hbitmap)

    try:
        bgra_data = convert_to_bgra(surface)
        ctypes.memmove(ppv_bits, bgra_data, width * height * 4)
        blend = BLENDFUNCTION()
        blend.BlendOp = AC_SRC_OVER
        blend.SourceConstantAlpha = 255
        blend.AlphaFormat = AC_SRC_ALPHA
        size = SIZE(width, height)
        src = POINT(0, 0)
        if window_x is not None and window_y is not None:
            dst = POINT(window_x, window_y)
        else:
            # 如果没有传递位置，使用 (0, 0) 或获取当前位置 (但我们知道 GetWindowRect 不可靠)
            dst = POINT(0, 0)

        user32.UpdateLayeredWindow(hwnd, hdc_screen, byref(dst), byref(size),
                                   hdc_mem, byref(src), 0, byref(blend), ULW_ALPHA)
    finally:
        gdi32.SelectObject(hdc_mem, old_bitmap)
        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)


# === 获取鼠标在屏幕上的绝对位置 ===
def get_mouse_screen_pos():
    """获取鼠标在屏幕上的绝对坐标"""
    point = POINT()
    user32.GetCursorPos(byref(point))
    return (point.x, point.y)


# === Pygame 初始化 ===
pygame.init()
WIDTH, HEIGHT = 144, 139
FPS = 12

# 创建隐藏的Pygame窗口用于图像处理
pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
hwnd = pygame.display.get_wm_info()["window"]

print("✅ 正在配置窗口样式...")

# 设置初始位置（屏幕中央）
screen_info = pygame.display.Info()
start_x = (screen_info.current_w - WIDTH) // 2
start_y = (screen_info.current_h - HEIGHT) // 2

# 🌟 关键：手动存储窗口的当前位置（使用列表方便修改）
current_window_pos = [start_x, start_y]

# 配置窗口样式
try:
    # === 修改窗口样式 ===
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_NOACTIVATE
    ex_style &= ~win32con.WS_EX_TRANSPARENT  # 确保可以接收点击事件
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    # 更新窗口位置
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        start_x, start_y,
        WIDTH, HEIGHT,
        win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE
    )

    print("✅ 桌宠窗口已配置：永远置顶、透明背景、隐藏任务栏")
except Exception as e:
    print(f"❌ 窗口配置失败: {e}")

# === 加载动画 ===
try:
    sprite_sheet = pygame.image.load("assets/idle_loop_fixed.png").convert_alpha()
    print("✅ 精灵表加载成功")
except Exception as e:
    print(f"❌ 加载精灵表失败: {e}. 创建测试图像...")
    sprite_sheet = pygame.Surface((575, 554), pygame.SRCALPHA)
    sprite_sheet.fill((0, 0, 0, 0))
    pygame.draw.circle(sprite_sheet, (255, 100, 100, 180), (287, 277), 200)
    pygame.draw.circle(sprite_sheet, (255, 255, 255, 128), (287, 277), 150)

FRAME_W, FRAME_H, COLUMNS, TARGET_FRAMES = 575, 554, 8, 120
frames = []
for y in range(0, sprite_sheet.get_height(), FRAME_H):
    for x in range(0, sprite_sheet.get_width(), FRAME_W):
        if len(frames) >= TARGET_FRAMES:
            break
        frame_rect = pygame.Rect(x, y, FRAME_W, FRAME_H)
        if frame_rect.width > 0 and frame_rect.height > 0:
            frames.append(sprite_sheet.subsurface(frame_rect).convert_alpha())

# 如果没提取到帧，创建默认帧
if not frames:
    test_frame = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    test_frame.fill((0, 0, 0, 0))
    pygame.draw.circle(test_frame, (255, 100, 100, 180), (WIDTH // 2, HEIGHT // 2), 50)
    frames = [test_frame]
else:
    # 缩放帧
    frames = [pygame.transform.smoothscale(f, (WIDTH, HEIGHT)).convert_alpha() for f in frames]

print(f"📊 成功提取 {len(frames)} 帧")

# === 动画循环 ===
TOTAL_FRAMES = len(frames)
frame_index = 0
direction = 1
clock = pygame.time.Clock()
running = True
dragging = False
drag_start_pos = None  # 拖动开始时鼠标的屏幕位置
drag_window_pos = None  # 拖动开始时窗口的位置

# 创建绘制表面
draw_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

while running:
    # 处理Pygame事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
            break

    # 获取鼠标状态
    mouse_pressed = pygame.mouse.get_pressed()[0]
    mouse_rel_pos = pygame.mouse.get_pos()  # 相对于窗口的位置

    if mouse_pressed:
        if not dragging:
            # 检测是否点击在精灵上
            current_frame = frames[frame_index]
            if is_click_on_sprite(mouse_rel_pos[0], mouse_rel_pos[1], current_frame):
                # 🌟 关键修正：在拖动开始时，使用 SetWindowPos 强制置顶并激活
                # 将 HWND_TOPMOST 作为一个Z序参数，配合 SWP_NOMOVE|SWP_NOSIZE
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST,
                                      0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                dragging = True
                pygame.event.set_grab(True)
                # 记录拖动开始时的位置
                drag_start_pos = get_mouse_screen_pos()
                drag_window_pos = (current_window_pos[0], current_window_pos[1])

                print(f"✅ 开始拖动 - 窗口实际位置: {drag_window_pos}")
    else:
        if dragging:
            dragging = False
            pygame.event.set_grab(False)
            drag_start_pos = None
            drag_window_pos = None
            print("停止拖动")

    # 处理拖动
    if dragging and mouse_pressed:
        try:
            # 获取当前鼠标屏幕位置
            current_mouse_pos = get_mouse_screen_pos()

            # 计算鼠标移动的距离
            dx = current_mouse_pos[0] - drag_start_pos[0]
            dy = current_mouse_pos[1] - drag_start_pos[1]

            # 计算新窗口位置
            new_x = drag_window_pos[0] + dx
            new_y = drag_window_pos[1] + dy

            # 边界检查（可选）
            # screen_info = pygame.display.Info()
            # new_x = max(0, min(new_x, screen_info.current_w - WIDTH))
            # new_y = max(0, min(new_y, screen_info.current_h - HEIGHT))

            print(f"拖动中 - dx: {dx}, dy: {dy}, New X: {new_x}, New Y: {new_y}")

            # 移动窗口
            # 参数: hwnd, x, y, width, height, repaint
            win32gui.SetWindowPos(hwnd, 0, new_x, new_y, WIDTH, HEIGHT, win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)

            # 🌟 关键修正：更新存储的窗口位置
            current_window_pos[0] = new_x
            current_window_pos[1] = new_y

        except Exception as e:
            print(f"拖动错误: {e}")

    # 更新动画帧
    frame_index += direction
    if frame_index >= TOTAL_FRAMES:
        direction = -1
        frame_index = TOTAL_FRAMES - 2
    elif frame_index < 0:
        direction = 1
        frame_index = 1

    draw_surface.fill((0, 0, 0, 0))
    draw_surface.blit(frames[frame_index], (0, 0))
    update_layered_window(hwnd, draw_surface, current_window_pos[0], current_window_pos[1])

    clock.tick(FPS)

# === 退出清理 ===
pygame.quit()
sys.exit()