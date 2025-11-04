import os
from PIL import Image
import math


def create_uniform_spritesheet(frames_dir, output_filepath, cols=8):
    """
    将目录中的所有 PNG 帧合并为一张精灵表，自动裁剪透明边框，并统一帧尺寸。

    Args:
        frames_dir (str): 包含单帧 PNG 图片的目录 (例如 'extracted_sprites')。
        output_filepath (str): 输出精灵表的路径 (例如 'assets/idle_loop_fixed.png')。
        cols (int): 精灵表中的列数。
    """
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
    if not frame_files:
        print(f"错误：在 {frames_dir} 中未找到任何 PNG 帧。")
        return

    cropped_frames_data = []
    max_cropped_width = 0
    max_cropped_height = 0

    print("第一阶段：加载、裁剪并计算最大帧尺寸...")
    for i, frame_file in enumerate(frame_files):
        frame_path = os.path.join(frames_dir, frame_file)
        with Image.open(frame_path) as img:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # 自动裁剪透明边框
            bbox = img.getbbox()  # 获取非透明区域的边界框 (left, upper, right, lower)
            if bbox:  # 如果存在非透明区域
                cropped_img = img.crop(bbox)
            else:  # 如果整个图像都是透明的，则保留原图 (或生成一个小的透明图)
                cropped_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))  # 创建一个 1x1 透明像素

            cropped_frames_data.append((cropped_img, bbox))  # 存储裁剪后的图像和原始边界框

            max_cropped_width = max(max_cropped_width, cropped_img.width)
            max_cropped_height = max(max_cropped_height, cropped_img.height)

    if not cropped_frames_data:
        print("没有找到有效的可裁剪帧。")
        return

    # 确定最终的统一帧尺寸
    # 可以根据原始帧的宽高比调整，这里我们使用最大裁剪尺寸作为统一尺寸
    UNIFORM_FRAME_WIDTH = math.ceil(max_cropped_width)
    UNIFORM_FRAME_HEIGHT = math.ceil(max_cropped_height)

    # 为了避免裁剪后尺寸过小而导致 Pygame 绘制问题，可以给 UNIFORM_FRAME_WIDTH 和 HEIGHT 设置一个最小值
    # 例如：UNIFORM_FRAME_WIDTH = max(max_cropped_width, 50)
    # UNIFORM_FRAME_HEIGHT = max(max_cropped_height, 50)

    num_frames = len(cropped_frames_data)
    rows = math.ceil(num_frames / cols)

    spritesheet_width = cols * UNIFORM_FRAME_WIDTH
    spritesheet_height = rows * UNIFORM_FRAME_HEIGHT

    spritesheet = Image.new('RGBA', (spritesheet_width, spritesheet_height), (0, 0, 0, 0))

    print(f"第二阶段：创建统一帧尺寸的精灵表: {num_frames} 帧，布局 {rows} 行 x {cols} 列，"
          f"统一帧尺寸 {UNIFORM_FRAME_WIDTH}x{UNIFORM_FRAME_HEIGHT}，总尺寸 {spritesheet_width}x{spritesheet_height}")

    for i, (cropped_img, original_bbox) in enumerate(cropped_frames_data):
        row = i // cols
        col = i % cols

        # 计算居中位置
        x_offset_in_frame = (UNIFORM_FRAME_WIDTH - cropped_img.width) // 2
        y_offset_in_frame = (UNIFORM_FRAME_HEIGHT - cropped_img.height) // 2

        # 计算在精灵表上的粘贴位置
        paste_x = col * UNIFORM_FRAME_WIDTH + x_offset_in_frame
        paste_y = row * UNIFORM_FRAME_HEIGHT + y_offset_in_frame

        spritesheet.paste(cropped_img, (paste_x, paste_y))

    spritesheet.save(output_filepath)
    print(f"✅ 成功创建统一尺寸的精灵表并保存到：{output_filepath}")


if __name__ == "__main__":
    FRAMES_FOLDER = "../extracted_sprites/dragging/1"
    OUTPUT_SPRITESHEET = "../assets/dragging_1.png"
    SPRITESHEET_COLS = 8

    create_uniform_spritesheet(FRAMES_FOLDER, OUTPUT_SPRITESHEET, cols=SPRITESHEET_COLS)