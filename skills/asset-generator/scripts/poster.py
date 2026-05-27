"""对接各平台自动发布"""
import json
from pathlib import Path

def post_to_platform(platform: str, output_dir: Path) -> bool:
    """
    发布到指定平台，返回成功/失败

    目前是占位实现，未来接入 baoyu-post-to-xiaohongshu, baoyu-post-to-x, baoyu-post-to-weibo。

    Args:
        platform: 平台名称 (xiaohongshu, x, weibo)
        output_dir: output/{game_id}/ 目录

    Returns:
        bool: 发布是否成功
    """
    highlights_path = output_dir / "highlights.md"
    images_dir = output_dir / "images"

    if not highlights_path.exists():
        print(f"Error: highlights.md not found in {output_dir}")
        return False

    print(f"[placeholder] Would post to {platform}:")
    print(f"  - highlights: {highlights_path}")
    print(f"  - images: {images_dir}")

    # 未来接入实际 API：
    # if platform == "xiaohongshu":
    #     from baoyu_post_to_xiaohongshu import post
    #     return post(highlights_path, images_dir)
    # elif platform == "x":
    #     from baoyu_post_to_x import post
    #     return post(highlights_path, images_dir)
    # elif platform == "weibo":
    #     from baoyu_post_to_weibo import post
    #     return post(highlights_path, images_dir)

    return True  # 占位总是返回成功


def post_all(output_dir: Path, platforms: list = None) -> dict:
    """
    发布到所有已配置平台

    Args:
        output_dir: output/{game_id}/ 目录
        platforms: 要发布的平台列表，默认全部

    Returns:
        dict: {platform: success} 映射
    """
    if platforms is None:
        platforms = ["xiaohongshu", "x", "weibo"]

    results = {}
    for platform in platforms:
        try:
            results[platform] = post_to_platform(platform, output_dir)
            status = "OK" if results[platform] else "FAILED"
            print(f"  {platform}: {status}")
        except Exception as e:
            results[platform] = False
            print(f"  {platform}: ERROR - {e}")

    return results


def notify_result(results: dict, game_id: str):
    """
    通知发布结果（目前是打印到 stdout，未来可接入 Telegram/邮件等）
    """
    print(f"\n=== Posting results for {game_id} ===")
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"Success: {success_count}/{total_count}")
    for platform, success in results.items():
        print(f"  {platform}: {'OK' if success else 'FAILED'}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
        output_dir = Path(f"output/{game_id}")
        results = post_all(output_dir)
        notify_result(results, game_id)
    else:
        print("Usage: python poster.py <game_id>")