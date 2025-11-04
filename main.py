# main.py

from pet_desktop import DesktopPet
import sys

# === Global Constants ===
WIDTH, HEIGHT = 144, 139   # Final window size
FPS = 12                   # Frame rate

# 🌟 新的动画资源配置字典 🌟
ANIMATION_CONFIG = {
    "idle": {
        "filepath": "assets/idle_loop_fixed.png",
        "frame_w": 575,
        "frame_h": 554,
        "total_frames": 120,
        "ranges": {"idle": (0, 119)}
    },
    "dragging": [
        {
            "prefix": "drag_A",
            "filepath": "assets/dragging_1(1).png",
            "frame_w": 575,
            "frame_h": 554,
            "total_frames": 120,
            "ranges": {
                "start": (0, 12),    # 抓起动画
                "hold": (12, 119),    # 保持循环
                "release": (0, 12)   # 释放动画（与 start 相同，但反向播放）
            }
        },
        {
            "prefix": "drag_B",
            "filepath": "assets/dragging_2(1).png",
            "frame_w": 575,
            "frame_h": 554,
            "total_frames": 120,
            "ranges": {
                "start": (0, 24),    # 抓起动画
                "hold": (24, 119),    # 保持循环
                "release": (0, 24)   # 释放动画（与 start 相同，但反向播放）
            }
        }
    ]
}

if __name__ == "__main__":
    try:
        pet = DesktopPet(
            width=WIDTH,
            height=HEIGHT,
            fps=FPS,
            animation_config=ANIMATION_CONFIG
        )
        pet.run()
    except Exception as e:
        print(f"Program startup failed or fatal error during runtime: {e}")
        sys.exit(1)