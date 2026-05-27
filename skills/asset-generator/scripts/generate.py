#!/usr/bin/env python3
"""
asset-generator/scripts/generate.py
读取 data/{game_id}/，生成 output/{game_id}/ 发布包

用法：
  python3 generate.py --game-id 169159534058 --date 2026-05-25
  python3 generate.py --game-id 169159534058 --date 2026-05-25 --skip-images --skip-post
"""
import argparse
import sys
from pathlib import Path

# 添加 scripts 目录到 path
sys.path.insert(0, str(Path(__file__).parent))

from review_writer import write_review
from data_extractor import write_data_json
from social_copywriter import write_highlights
from image_generator import (
    generate_infographic,
    generate_thumbnail,
    write_board_screenshot,
    write_blunder_images,
)
from poster import post_all, notify_result


def parse_args():
    parser = argparse.ArgumentParser(description="Generate content package from chess analysis data")
    parser.add_argument("--game-id", required=True, help="Game ID (e.g., 169159534058)")
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format (e.g., 2026-05-25)")
    parser.add_argument("--skip-images", action="store_true", help="Skip image generation")
    parser.add_argument("--skip-post", action="store_true", help="Skip platform posting")
    parser.add_argument("--data-dir", default="data", help="Data directory (default: data)")
    parser.add_argument("--output-dir", default="output", help="Output directory (default: output)")
    return parser.parse_args()


def main():
    args = parse_args()

    # 构建 game_id（格式：{date}_{game_id}）
    game_id = f"{args.date}_{args.game_id}"

    # 检查 data 目录
    data_dir = Path(args.data_dir) / game_id
    if not data_dir.exists():
        print(f"Error: data directory not found: {data_dir}")
        print(f"  chess-analysis skill may not have run yet for this game.")
        return 1

    # 检查必需文件
    required_files = ["metadata.json", "engine_eval.json"]
    missing = [f for f in required_files if not (data_dir / f).exists()]
    if missing:
        print(f"Error: missing required files in {data_dir}: {missing}")
        return 1

    # 创建 output 目录
    output_dir = Path(args.output_dir) / game_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "images").mkdir(exist_ok=True)

    print(f"Generating content package for {game_id}...")
    print(f"  Data: {data_dir}")
    print(f"  Output: {output_dir}")

    # 检查是否已生成过（幂等性）
    review_exists = (output_dir / "review.md").exists()
    data_json_exists = (output_dir / "data.json").exists()
    if review_exists and data_json_exists and not args.skip_images:
        print(f"Output already exists, skipping generation. Use --skip-images to regenerate.")
        print(f"  Remove files in {output_dir} to regenerate.")
    else:
        # 生成 review.md
        print("Generating review.md...")
        try:
            write_review(game_id, output_dir)
            print("  review.md OK")
        except Exception as e:
            print(f"  review.md FAILED: {e}")

        # 生成 data.json
        print("Generating data.json...")
        try:
            write_data_json(game_id, output_dir)
            print("  data.json OK")
        except Exception as e:
            print(f"  data.json FAILED: {e}")

        # 生成 highlights.md
        print("Generating highlights.md...")
        try:
            write_highlights(game_id, output_dir)
            print("  highlights.md OK")
        except Exception as e:
            print(f"  highlights.md FAILED: {e}")

    # 生成图片
    if not args.skip_images:
        print("Generating images...")
        try:
            write_board_screenshot(game_id, output_dir)
            print("  board.png OK")
        except Exception as e:
            print(f"  board.png FAILED: {e}")

        try:
            generate_infographic(game_id, output_dir)
            print("  infographic OK")
        except Exception as e:
            print(f"  infographic FAILED: {e}")

        try:
            generate_thumbnail(game_id, output_dir)
            print("  thumbnail OK")
        except Exception as e:
            print(f"  thumbnail FAILED: {e}")

        try:
            blunder_images = write_blunder_images(game_id, output_dir)
            if blunder_images:
                print(f"  blunder images: {len(blunder_images)} copied")
        except Exception as e:
            print(f"  blunder images FAILED: {e}")

    print(f"\nOutput written to {output_dir}")

    # 发布
    if not args.skip_post:
        print("\nPosting to platforms...")
        results = post_all(output_dir)
        notify_result(results, game_id)
    else:
        print("\nSkipping post (--skip-post)")

    return 0


if __name__ == "__main__":
    sys.exit(main())