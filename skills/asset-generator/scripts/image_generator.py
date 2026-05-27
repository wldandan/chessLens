"""生成 images/ 目录下的图片素材"""
import json
from pathlib import Path

def generate_infographic(game_id: str, output_dir: Path):
    """
    生成评估曲线/失误分布 infographic.png

    目前是占位实现，未来可接入 baoyu-imagine 或 matplotlib 生成图片。
    """
    data_dir = Path(f"data/{game_id}")
    engine_eval_path = data_dir / "engine_eval.json"

    output_path = output_dir / "images"
    output_path.mkdir(parents=True, exist_ok=True)

    # 占位：生成一个简单的文本文件说明
    placeholder_file = output_path / "infographic_placeholder.txt"
    placeholder_file.write_text(
        f"infographic for game {game_id}\n"
        f"Generated at: {__import__('datetime').datetime.now()}\n"
        f"Todo: integrate with baoyu-imagine or matplotlib",
        encoding="utf-8"
    )
    print(f"Infographic placeholder created at {placeholder_file}")
    return placeholder_file


def generate_thumbnail(game_id: str, output_dir: Path):
    """
    生成视频封面 thumbnail.jpg

    目前是占位实现，未来可接入 baoyu-imagine 生成封面。
    """
    output_path = output_dir / "images"
    output_path.mkdir(parents=True, exist_ok=True)

    # 占位
    placeholder_file = output_path / "thumbnail_placeholder.txt"
    placeholder_file.write_text(
        f"thumbnail for game {game_id}\n"
        f"Generated at: {__import__('datetime').datetime.now()}\n"
        f"Todo: integrate with baoyu-imagine",
        encoding="utf-8"
    )
    print(f"Thumbnail placeholder created at {placeholder_file}")
    return placeholder_file


def write_board_screenshot(game_id: str, output_dir: Path):
    """
    将棋盘截图复制到 output/images/board.png

    从 docs/reviews/images/ 复制已有截图。
    """
    # 尝试多个可能的位置
    possible_sources = [
        Path(f"docs/reviews/images/{game_id}.png"),
        Path(f"docs/reviews/images/{game_id.split('_')[1] if '_' in game_id else game_id}.png"),
        Path(f"~/chessLens/chess-reviews-summary/images/{game_id}.png").expanduser(),
    ]

    output_path = output_dir / "images"
    output_path.mkdir(parents=True, exist_ok=True)

    for src in possible_sources:
        if src.exists():
            dst = output_path / "board.png"
            dst.write_bytes(src.read_bytes())
            print(f"Board screenshot copied from {src} to {dst}")
            return dst

    # 没找到截图，创建占位文件
    placeholder_file = output_path / "board_placeholder.txt"
    placeholder_file.write_text(
        f"Board screenshot for game {game_id} not found in expected locations.",
        encoding="utf-8"
    )
    print(f"Board screenshot not found, placeholder created at {placeholder_file}")
    return placeholder_file


def write_blunder_images(game_id: str, output_dir: Path):
    """
    复制失误对比图（如果有）到 output/images/

    从 docs/reviews/images/ 查找并复制 blunder_N.png 类型的文件。
    """
    output_path = output_dir / "images"
    output_path.mkdir(parents=True, exist_ok=True)

    # 提取实际 game_id
    actual_game_id = game_id.split("_")[1] if "_" in game_id else game_id

    images_dir = Path("docs/reviews/images")
    if not images_dir.exists():
        return []

    copied = []
    for img_file in images_dir.iterdir():
        if actual_game_id in img_file.name and "blunder" in img_file.name:
            dst = output_path / img_file.name
            dst.write_bytes(img_file.read_bytes())
            copied.append(dst)

    return copied