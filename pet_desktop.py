# pet_desktop.py

import pygame
import sys
import win32con
import win32gui
# Import created modules
import window_manager as wm
from pet_states import IdleState
from sprite_animation import load_frames_from_sheet, AnimationController


class DesktopPet:
    def __init__(self, width, height, fps, animation_config):
        pygame.init()
        self.width = width
        self.height = height
        self.fps = fps
        self.running = True
        self.clock = pygame.time.Clock()

        # 1. Initialize hidden Pygame window
        pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        self.hwnd = pygame.display.get_wm_info()["window"]
        print("✅ Pygame window created")

        # 2. Calculate initial position (screen center)
        screen_info = pygame.display.Info()
        start_x = (screen_info.current_w - self.width) // 2
        start_y = (screen_info.current_h - self.height) // 2

        # Store current window position (mutable list)
        self.current_window_pos = [start_x, start_y]

        # 3. Configure layered window style
        try:
            wm.setup_layered_window(self.hwnd, self.width, self.height, start_x, start_y)
        except Exception as e:
            print(f"❌ Window configuration failed: {e}")

        # 4. Load animation resources
        all_animations = {}
        # --- 加载 Idle 动画 ---
        idle_config = animation_config["idle"]
        idle_frames = load_frames_from_sheet(
            idle_config["filepath"], idle_config["frame_w"], idle_config["frame_h"],
            self.width, self.height, idle_config["total_frames"]
        )
        all_animations['idle'] = idle_frames

        # 🌟 存储所有动画的范围（包括 idle）
        self.animation_ranges = {"idle": idle_config["ranges"]["idle"]}

        # 🌟 关键修改：加载所有 Dragging 动作 🌟
        dragging_options = animation_config["dragging"]

        # 新增属性：存储所有可用的拖动前缀 (例如 ['drag_A', 'drag_B'])
        self.available_drag_prefixes = []

        for group in dragging_options:
            prefix = group["prefix"]
            self.available_drag_prefixes.append(prefix)
            print(f"🎨 Loading ALL dragging group: {prefix}")

            # --- 加载该组的精灵表 ---
            drag_frames = load_frames_from_sheet(
                group["filepath"],
                group["frame_w"],
                group["frame_h"],
                self.width,
                self.height,
                group["total_frames"]
            )
            frame_key = f"{prefix}_frames"
            # 只有当 drag_frames 不为空时才添加到 all_animations 字典
            if drag_frames:
                all_animations[frame_key] = drag_frames
            else:
                print(f"❌ WARNING: {prefix} frames list is empty. Check sprite sheet.")

            # 🌟 新增调试打印 🌟
            print(f"DEBUG: Stored frames for key '{frame_key}'. List length: {len(drag_frames)}")

            # --- 存储帧范围 ---
            for sub_name, ranges in group["ranges"].items():
                # 存储每个子序列的范围，例如: self.animation_ranges['drag_A_start']
                self.animation_ranges[f"{prefix}_{sub_name}"] = ranges

        self.animator = AnimationController(all_animations, self.animation_ranges)  # 初始化新的控制器

        # 5. Dragging state management
        self.drag_start_pos = None  # Mouse screen position at drag start
        self.drag_window_pos = None  # Window position at drag start

        # 6. Drawing surface (for transparent rendering)
        self.draw_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        self.state = None
        self.change_state(IdleState(self))

    def change_state(self, new_state):
        """切换到新的宠物状态。"""
        if self.state is not None:
            self.state.exit()

        self.state = new_state
        self.state.enter()

    def is_click_on_sprite(self, mouse_x, mouse_y):
        """Checks if the mouse click is on a non-transparent area of the sprite."""
        current_frame = self.animator.get_current_frame()
        # Check if within window bounds
        if 0 <= mouse_x < self.width and 0 <= mouse_y < self.height:
            try:
                # Get Alpha value at the click position
                pixel_color = current_frame.get_at((mouse_x, mouse_y))
                alpha = pixel_color[3]  # Alpha channel
                return alpha > 10
            except IndexError:
                return False
        return False

    def render(self):
        """Renders the current frame to the layered window."""
        # 1. Draw current frame to Surface
        self.draw_surface.fill((0, 0, 0, 0))  # Clear Surface with transparent color
        self.draw_surface.blit(self.animator.get_current_frame(), (0, 0))

        # 2. Call window_manager to update the layered window
        wm.update_layered_window(
            self.hwnd,
            self.draw_surface,
            self.current_window_pos[0],
            self.current_window_pos[1]
        )

    def run(self):
        """Main application loop."""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
                    break
            if not self.running:
                break

            self.state.handle_input()
            self.state.update()

            self.render()

            self.clock.tick(self.fps)

        self.cleanup()

    def cleanup(self):
        """Cleanup resources upon exit."""
        pygame.quit()
        sys.exit()