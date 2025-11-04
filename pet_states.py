# pet_states.py

import win32con
import win32gui
import pygame
import random
import window_manager as wm


class PetState:
    """状态机的抽象基类 (Base Class for Pet States)."""

    def __init__(self, pet_context):
        self.pet = pet_context  # 引用 DesktopPet 实例，以便访问其属性和方法 (e.g., self.pet.animator)

    def enter(self):
        """进入该状态时执行的初始化逻辑 (Logic executed upon entering the state)."""
        pass

    def exit(self):
        """退出该状态时执行的清理逻辑 (Logic executed upon exiting the state)."""
        pass

    def handle_input(self):
        """处理输入事件和状态切换 (Handles input events and state transitions)."""
        pass

    def update(self):
        """每帧更新状态逻辑 (Updates state logic every frame)."""
        # 通常在这里调用 self.pet.animator.update_frame()
        self.pet.animator.update_frame()


# --- 具体状态实现 (Concrete State Implementations) ---

class IdleState(PetState):
    """宠物闲置状态：播放待机动画，等待拖动或自动行为。"""

    def enter(self):
        print("🤖 State: Entering Idle.")
        # 可能加载 Idle 专有的动画序列
        self.pet.animator.set_animation('idle')

    def handle_input(self):
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_rel_pos = pygame.mouse.get_pos()

        if mouse_pressed:
            current_frame = self.pet.animator.get_current_frame()

            # 使用 DesktopPet 的点击检测方法
            if self.pet.is_click_on_sprite(mouse_rel_pos[0], mouse_rel_pos[1]):
                # 切换到 DraggingState
                self.pet.change_state(DraggingState(self.pet))

    def update(self):
        super().update()
        # Idle 状态可能包含随机行为的定时器逻辑，例如：
        # if timer_is_up:
        #     self.pet.change_state(WalkingState(self.pet))


class DraggingState(PetState):
    """宠物拖动状态：被鼠标按住并移动。"""

    def enter(self):
        print("🤖 State: Entering Dragging.")

        # 强制置顶，确保在拖动开始时窗口能捕获鼠标 (从 handle_input 移到 enter)
        win32gui.SetWindowPos(self.pet.hwnd, win32con.HWND_TOPMOST,
                              0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

        # 记录拖动开始时的位置 (从 handle_input 移到 enter)
        self.pet.drag_start_pos = wm.get_mouse_screen_pos()
        self.pet.drag_window_pos = (self.pet.current_window_pos[0], self.pet.current_window_pos[1])
        # 1. 启动抓起动画 (单次播放)
        # 🌟 关键：从可用列表中随机选择一个前缀 🌟
        selected_prefix = random.choice(self.pet.available_drag_prefixes)

        # 存储当前组的完整动画名称
        self.start_anim_name = f"{selected_prefix}_start"
        self.hold_anim_name = f"{selected_prefix}_hold"
        self.release_anim_name = f"{selected_prefix}_release"
        self.pet.animator.set_animation(self.start_anim_name)
        # 3. 追踪当前子状态
        self.current_drag_stage = 'start'
        self.can_release = False  # 🌟 新增：初始状态下不允许释放 🌟

    def exit(self):
        print("🤖 State: Exiting Dragging.")

        self.pet.drag_start_pos = None
        self.pet.drag_window_pos = None

    def handle_input(self):
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if not mouse_pressed and self.current_drag_stage != 'release' and self.can_release:
            self.pet.animator.set_animation(self.release_anim_name)
            self.current_drag_stage = 'release'
            self.can_release = False

    def update(self):
        super().update()
        if self.current_drag_stage == 'release':
            # 🌟 临时调试代码：检查释放动画是否结束 🌟
            if self.pet.animator.is_finished:
                print("DEBUG: Release animation finished! Should switch to Idle.")
        # 1. 检查动画是否完成，并切换子序列
        next_sequence = self.pet.animator.check_finished_and_advance()
        if next_sequence:
            if next_sequence == 'hold':
                print("DEBUG: Start animation finished. Switching to HOLD.")
                # 抓取播放完毕，切换到循环保持动画
                self.pet.animator.set_animation(self.hold_anim_name)  # 使用通用的 'dragging_hold'
                self.current_drag_stage = 'hold'
                self.can_release = True

            elif next_sequence == 'idle':
                print("DEBUG: Animator returned 'idle'. Switching state now.")
                # 释放动画播放完毕，切换到主 Idle 状态
                self.pet.change_state(IdleState(self.pet))
                return
        # 执行原有的拖动位置更新逻辑
        if self.current_drag_stage == 'start' or self.current_drag_stage == 'hold':
            self._update_position()

    def _update_position(self):
        """处理拖动时的位置更新、边界检查、弹性和平滑移动。"""
        try:
            # Get current absolute mouse position
            current_mouse_pos = wm.get_mouse_screen_pos()

            # Calculate mouse movement distance
            dx = current_mouse_pos[0] - self.pet.drag_start_pos[0]
            dy = current_mouse_pos[1] - self.pet.drag_start_pos[1]

            # Calculate new window position (基于拖动起始位置)
            new_x = self.pet.drag_window_pos[0] + dx
            new_y = self.pet.drag_window_pos[1] + dy

            # --- for debug ---
            # print(f"原始坐标: ({new_x}, {new_y})")
            # print(f"窗口尺寸: {self.pet.width} x {self.pet.height}")

            # get max screen resolution
            screen_modes = pygame.display.get_desktop_sizes()
            # Note: list_modes/get_desktop_sizes() usually returns [(width, height), ...]
            if screen_modes and screen_modes[0] != -1:
                screen_width, screen_height = screen_modes[0]
            else:
                # 兜底：使用 Info() 或默认值
                screen_width = pygame.display.Info().current_w
                screen_height = pygame.display.Info().current_h

            # --- 弹性边界和平滑移动逻辑 ---

            # 弹性边界参数
            ELASTIC_MARGIN = 64
            ELASTIC_STRENGTH = 0.6489

            # 计算弹性偏移
            elastic_dx, elastic_dy = 0, 0

            # 左边界弹性
            if new_x < ELASTIC_MARGIN:
                elastic_dx = (ELASTIC_MARGIN - new_x) * ELASTIC_STRENGTH

            # 右边界弹性
            elif new_x > screen_width - self.pet.width - ELASTIC_MARGIN:
                elastic_dx = -(new_x - (screen_width - self.pet.width - ELASTIC_MARGIN)) * ELASTIC_STRENGTH

            # 上边界弹性
            if new_y < ELASTIC_MARGIN:
                elastic_dy = (ELASTIC_MARGIN - new_y) * ELASTIC_STRENGTH

            # 下边界弹性
            elif new_y > screen_height - self.pet.height - ELASTIC_MARGIN:
                elastic_dy = -(new_y - (screen_height - self.pet.height - ELASTIC_MARGIN)) * ELASTIC_STRENGTH

            # 应用弹性偏移
            new_x += elastic_dx
            new_y += elastic_dy

            # Boundary Check (强制限制在屏幕内，防止被弹性推太远)
            target_x = max(0, min(new_x, screen_width - self.pet.width))
            target_y = max(0, min(new_y, screen_height - self.pet.height))

            # 平滑移动逻辑
            SMOOTH_FACTOR = 0.367

            # !!! 关键修复: 将 current_smooth_pos 设为 DesktopPet 的属性 !!!
            # 必须使用 hasattr(self.pet, 'current_smooth_pos') 检查并设置
            if not hasattr(self.pet, 'current_smooth_pos'):
                self.pet.current_smooth_pos = [target_x, target_y]

            # 平滑移动到目标位置
            self.pet.current_smooth_pos[0] += (target_x - self.pet.current_smooth_pos[0]) * SMOOTH_FACTOR
            self.pet.current_smooth_pos[1] += (target_y - self.pet.current_smooth_pos[1]) * SMOOTH_FACTOR

            final_x = int(self.pet.current_smooth_pos[0])
            final_y = int(self.pet.current_smooth_pos[1])

            # Move window
            wm.set_window_position(self.pet.hwnd, final_x, final_y, self.pet.width, self.pet.height)

            # Update stored window position
            self.pet.current_window_pos[0] = final_x
            self.pet.current_window_pos[1] = final_y

        except Exception as e:
            print(f"Dragging error: {e}")
            self.pet.change_state(IdleState(self.pet))  # 安全回退
