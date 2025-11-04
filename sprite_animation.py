# sprite_animation.py

import pygame
import math

def load_frames_from_sheet(filepath, frame_w, frame_h, target_w, target_h, target_frames):
    """
    Loads, extracts, and scales animation frames from a sprite sheet.
    Creates default test frames if loading fails.
    """
    frames = []
    frame_w = math.ceil(frame_w)
    frame_h = math.ceil(frame_h)

    try:
        sprite_sheet = pygame.image.load(filepath).convert_alpha()
        print(f"✅ Sprite sheet '{filepath}' loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load sprite sheet: {e}. Creating test image...")
        # Create a test Surface matching the frame size
        sprite_sheet = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        sprite_sheet.fill((0, 0, 0, 0))
        # Draw a visible test shape
        pygame.draw.circle(sprite_sheet, (255, 100, 100, 180), (frame_w // 2, frame_h // 2), frame_w // 2 - 1)

        # If loading failed, use the single test frame and scale it
        frames.append(sprite_sheet)
        return [pygame.transform.smoothscale(f, (target_w, target_h)).convert_alpha() for f in frames]

    # Iterate through the sprite sheet to extract frames
    for y in range(0, sprite_sheet.get_height(), frame_h):
        for x in range(0, sprite_sheet.get_width(), frame_w):
            if len(frames) >= target_frames:
                break

            frame_rect = pygame.Rect(x, y, frame_w, frame_h)

            if frame_rect.width > 0 and frame_rect.height > 0:
                # Extract and convert frame to alpha format
                frame = sprite_sheet.subsurface(frame_rect).convert_alpha()
                frames.append(frame)
        if len(frames) >= target_frames:
            break

    # Fallback if no frames were extracted
    if not frames:
        test_frame = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        test_frame.fill((0, 0, 0, 0))
        pygame.draw.circle(test_frame, (255, 100, 100, 180), (target_w // 2, target_h // 2), 50)
        frames = [test_frame]
    else:
        # Scale all extracted frames to the target dimension
        frames = [pygame.transform.smoothscale(f, (target_w, target_h)).convert_alpha() for f in frames]

    print(f"📊 Successfully extracted {len(frames)} frames")
    return frames


class AnimationController:
    """
    Manages multiple animation sequences (loaded from different sprite sheets)
    and handles frame indexing and looping rules.
    """
    ANIMATION_RULES = {
        'idle': {'type': 'loop_reverse'},
        'start': {'type': 'one_shot', 'next': 'hold'},
        'hold': {'type': 'loop_reverse'},
        'release': {'type': 'one_shot_reverse', 'next': 'idle'},
    }

    def __init__(self, animations_data, animation_ranges):
        """
        animations_data: {name: frames_list}
        """
        self.animations = animations_data
        self.animation_ranges = animation_ranges
        self.current_sequence_name = None

        # 🌟 运行时状态 (Run-time State)
        self.current_frames = []
        self.total_frames = 0
        self.current_index = 0
        self.direction = 1  # 1: forward, -1: reverse
        self.start_frame = 0  # 🌟 新增：当前序列的播放起始帧
        self.end_frame = 0  # 🌟 新增：当前序列的播放结束帧

    def set_animation(self, sequence_name):
        """
        Switches to a new animation sequence and resets index.
        """
        if sequence_name == self.current_sequence_name:
            return

            # 🌟 关键修复 1: 检查是否为复合名称 (如 drag_A_start)
        parts = sequence_name.split('_')

        if len(parts) >= 3 and (parts[0] == 'drag' or parts[0] == 'drag'):  # 假设拖动前缀是 drag_X_
            # 这是一个拖动动作的子序列
            prefix = f"{parts[0]}_{parts[1]}"  # 例如 'drag_A'
            sub_name = parts[2]  # 例如 'start'
            frame_source_name = f"{prefix}_frames"  # 例如 'drag_A_frames'
        else:
            # 这是一个简单名称，如 'idle'
            prefix = None
            sub_name = sequence_name
            frame_source_name = sequence_name  # 'idle' -> 'idle'

        rule = self.ANIMATION_RULES.get(sub_name)

        if not rule:
            print(f"⚠️ Rule for '{sub_name}' not found.")
            return

        # 1. 确定帧列表和帧范围
        if frame_source_name not in self.animations:
            print(f"⚠️ Frame source '{frame_source_name}' not loaded.")
            return

        self.current_sequence_name = sequence_name
        self.current_frames = self.animations[frame_source_name]
        self.total_frames = len(self.current_frames)

        # 从 ranges 字典中获取播放范围
        if sequence_name in self.animation_ranges:
            self.start_frame, self.end_frame = self.animation_ranges[sequence_name]
        else:
            # 兜底：使用整个帧列表
            self.start_frame, self.end_frame = 0, self.total_frames - 1

        # 2. 设置播放状态和方向
        self.is_playing_one_shot = (rule['type'] == 'one_shot' or rule['type'] == 'one_shot_reverse')
        self.is_finished = False

        if rule['type'] == 'one_shot_reverse':
            # 释放动画：从当前hold的帧开始，反向播到 start_frame（例如 0 帧）
            # 关键：从当前索引开始反向播放，但不能超过 end_frame
            self.current_index = min(int(self.current_index), self.end_frame)
            self.direction = -1
        else:
            # start/hold 动画：从起始帧开始播放
            self.current_index = self.start_frame
            self.direction = 1

        print(f"📊 Switched to: {sequence_name} (Range: {self.start_frame}-{self.end_frame}, Type: {rule['type']})")

    def update_frame(self):
        """
        Updates the animation frame index for the current sequence.
        """
        if self.total_frames <= 1 or self.is_finished:
            return

        self.current_index += self.direction

        # --- 🌟 单次动画处理 (One-Shot Logic) 🌟 ---
        if self.is_playing_one_shot:
            print(f"DEBUG: Current sequence '{self.current_sequence_name}' is One-Shot.")
            # 正向播放，到达末尾
            if self.direction == 1 and self.current_index > self.end_frame:
                self.current_index = self.end_frame
                self.is_finished = True

            # 反向播放，到达起始
            elif self.direction == -1 and self.current_index < self.start_frame:
                self.current_index = self.start_frame
                self.is_finished = True

            return

        # --- 循环动画处理 (Loop Logic) ---
        print(f"DEBUG: Current sequence '{self.current_sequence_name}' is LOOPING.")
        # 循环播放，到达末尾
        if self.current_index > self.end_frame:
            self.direction = -1
            self.current_index = self.end_frame - 1 if self.end_frame > self.start_frame else self.start_frame

        # 循环播放，到达起始
        elif self.current_index < self.start_frame:
            self.direction = 1
            self.current_index = self.start_frame + 1 if self.end_frame > self.start_frame else self.start_frame

    def get_current_frame(self):
        """Returns the current Pygame Surface."""
        if not self.current_frames:
            # 安全返回一个空 Surface
            return pygame.Surface((1, 1), pygame.SRCALPHA)

        index = max(0, min(int(self.current_index), self.total_frames - 1))
        return self.current_frames[index]

    def check_finished_and_advance(self):
        """
        检查单次动画是否完成。在 pet_states.py 中调用。
        如果完成，返回下一个动作名称 (例如 'dragging_hold')。
        """
        if self.is_finished:
            sequence_name = self.current_sequence_name
            parts = sequence_name.split('_')

            # 如果是拖动动作 (e.g., drag_A_release)，则获取子序列名 'release'
            if len(parts) >= 3 and parts[0] == 'drag':
                sub_name = parts[2]
            else:
                sub_name = sequence_name  # 如果是 'idle' 或其他简单名称

            rule = self.ANIMATION_RULES.get(sub_name)

            # 🌟 关键：重置 finished 标志，防止在下一帧再次触发
            self.is_finished = False

            # 检查规则中是否有明确的下一个状态
            if rule and 'next' in rule:
                return rule['next']

            # 如果是单次播放但没有定义 'next'，默认返回 None
            return None
        return None