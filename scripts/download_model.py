#!/usr/bin/env python3
"""并行、可断点续传地下载 Hugging Face 模型文件，并可选校验完整性。

用法：
    python download_model.py --repo Systran/faster-whisper-large-v3 --dest ./models/large-v3 --verify
    python download_model.py --repo Systran/faster-whisper-large-v3 --list

断点续传依赖目标文件旁的 <文件名>.progress.json，中断后重跑同一命令即可继续。
"""

import argparse
import hashlib
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request

try:
    import certifi
except ImportError:  # 没有 certifi 时退回系统证书
    certifi = None

DEFAULT_FILES = [
    "config.json",
    "model.bin",
    "preprocessor_config.json",
    "tokenizer.json",
    "vocabulary.json",
]

CHUNK = 1 << 20
MIN_PART = 4 << 20


def ssl_context():
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


CONTEXT = ssl_context()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", required=True, help="Hugging Face 仓库，如 Systran/faster-whisper-large-v3")
    parser.add_argument("--dest", help="下载目录")
    parser.add_argument("--files", help="逗号分隔的文件名，默认为 faster-whisper 需要的几个文件")
    parser.add_argument("--conns", type=int, default=8, help="并行连接数，默认 8")
    parser.add_argument("--host", default=None, help="镜像站点，默认依次尝试 huggingface.co 与 hf-mirror.com")
    parser.add_argument("--timeout", type=int, default=30, help="单次读取超时秒数，默认 30")
    parser.add_argument("--verify", action="store_true", help="下载后用 Hugging Face 上的 sha256 校验文件")
    parser.add_argument("--list", action="store_true", dest="list_files", help="只列出仓库文件与大小")
    parser.add_argument("--force", action="store_true", help="已存在的文件也重新下载")
    return parser.parse_args(argv)


def hosts_for(args):
    if args.host:
        return [args.host.rstrip("/")]
    return ["https://huggingface.co", "https://hf-mirror.com"]


def url_for(args, name, host):
    return "%s/%s/resolve/main/%s" % (host, args.repo, name)


def open_url(args, name, headers=None, timeout=None, tries=25):
    timeout = timeout or args.timeout
    hosts = hosts_for(args)
    last = None
    for attempt in range(tries):
        host = hosts[0] if attempt < max(tries - 3, 1) else hosts[-1]
        request = urllib.request.Request(url_for(args, name, host), headers=headers or {})
        try:
            return urllib.request.urlopen(request, timeout=timeout, context=CONTEXT)
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                raise RuntimeError("仓库 %s 里没有 %s（HTTP %d）" % (args.repo, name, exc.code))
            last = exc
            time.sleep(min(0.5 + 0.5 * attempt, 3))
        except Exception as exc:  # 网络代理会间歇性重置连接，直接重试
            last = exc
            time.sleep(min(0.5 + 0.5 * attempt, 3))
    raise RuntimeError("无法访问 %s：%s" % (name, last))


def remote_size(args, name):
    with open_url(args, name, {"Range": "bytes=0-0"}, timeout=30) as response:
        if response.status == 206:
            return int(response.headers["Content-Range"].split("/")[-1])
        return int(response.headers["Content-Length"])


def repo_metadata(args):
    url = "https://huggingface.co/api/models/%s?blobs=true" % args.repo
    last = None
    for attempt in range(10):
        try:
            request = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=30, context=CONTEXT) as response:
                return json.load(response)
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(min(1 + attempt, 6))
    raise RuntimeError("无法读取仓库信息：%s" % last)


def repo_metadata_safe(args):
    """读取仓库信息；网络不通时返回 None，由调用方按给定文件名继续。"""
    try:
        return repo_metadata(args)
    except RuntimeError as exc:
        print("提示：读取仓库文件列表失败（%s），按给定文件名直接下载。" % exc, flush=True)
        return None


def resolve_names(candidates, available):
    """把候选文件名映射成仓库里真实存在的文件，缺失的同名家族自动替换。"""
    if available is None:
        return list(candidates), []
    resolved, missing = [], []
    for candidate in candidates:
        if candidate in available:
            resolved.append(candidate)
            continue
        stem = os.path.splitext(candidate)[0]
        family = [name for name in available if os.path.splitext(name)[0] == stem]
        if len(family) == 1:
            resolved.append(family[0])
        else:
            missing.append(candidate)
    return resolved, missing


def make_plan(size, conns):
    parts = max(1, min(conns, size // MIN_PART))
    chunk = max(-(-size // parts), 1)
    plan, start = [], 0
    while start < size:
        end = min(start + chunk - 1, size - 1)
        plan.append([start, end])
        start = end + 1
    return plan


def load_state(path, size, conns):
    side = path + ".progress.json"
    plan = make_plan(size, conns)
    if os.path.exists(side) and os.path.exists(path):
        try:
            with open(side, encoding="utf-8") as handle:
                state = json.load(handle)
            if state.get("size") == size and state.get("ranges") == plan and len(state["done"]) == len(plan):
                return state, side
        except Exception:  # noqa: BLE001
            pass
    return {"size": size, "ranges": plan, "done": [0] * len(plan)}, side


def save_state(state, side):
    tmp = side + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(state, handle)
    os.replace(tmp, side)


def download_part(args, name, path, start, end, state, index, lock, stop):
    position = start + state["done"][index]
    failures = 0
    while position <= end and not stop.is_set():
        try:
            headers = {"Range": "bytes=%d-%d" % (position, end)}
            with open_url(args, name, headers, tries=10) as response, open(path, "r+b") as handle:
                handle.seek(position)
                while position <= end:
                    chunk = response.read(min(CHUNK, end - position + 1))
                    if not chunk:
                        break
                    handle.write(chunk)
                    position += len(chunk)
                    with lock:
                        state["done"][index] = position - start
                handle.flush()
            failures = 0
        except Exception as exc:  # noqa: BLE001
            failures += 1
            if failures >= 6:
                stop.set()
                raise RuntimeError("第 %d 段下载失败：%s" % (index, exc))
            time.sleep(min(2 * failures, 8))
    if position <= end:
        raise RuntimeError("第 %d 段未下载完" % index)


def fetch(args, name, dest_dir, size=None):
    path = os.path.join(dest_dir, name)
    size = size or remote_size(args, name)
    side_path = path + ".progress.json"
    resuming = os.path.exists(side_path)
    state, side = load_state(path, size, args.conns)
    done_total = sum(state["done"])

    already_there = os.path.exists(path) and os.path.getsize(path) == size
    if already_there and not args.force and (not resuming or done_total == size):
        if resuming:
            os.remove(side)
        print("已存在且完整，跳过：%s" % name, flush=True)
        return

    if args.force or not already_there:
        with open(path, "wb") as handle:
            handle.truncate(size)
        state["done"] = [0] * len(state["ranges"])
        save_state(state, side)

    print(
        "开始下载：%s（%.1f MB，续传起点 %.1f MB）" % (name, size / 1e6, done_total / 1e6),
        flush=True,
    )
    lock = threading.Lock()
    stop = threading.Event()
    began = time.time()
    threads = [
        threading.Thread(
            target=download_part,
            args=(args, name, path, part[0], part[1], state, index, lock, stop),
            daemon=True,
        )
        for index, part in enumerate(state["ranges"])
    ]
    for thread in threads:
        thread.start()

    while any(thread.is_alive() for thread in threads):
        time.sleep(5)
        with lock:
            current = sum(state["done"])
            save_state(state, side)
        print(
            "  %s：%5.1f/%5.1f MB  %.2f MB/s"
            % (name, current / 1e6, size / 1e6, (current - done_total) / 1e6 / max(time.time() - began, 1e-3)),
            flush=True,
        )
    for thread in threads:
        thread.join()

    if stop.is_set():
        raise RuntimeError("下载中断：%s" % name)
    with lock:
        final = sum(state["done"])
    if final != size:
        raise RuntimeError("%s 只写入 %d/%d 字节" % (name, final, size))
    if os.path.exists(side):
        os.remove(side)
    print("完成：%s（%.1f MB，用时 %.0fs）" % (name, size / 1e6, time.time() - began), flush=True)


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(args, dest_dir, names, metadata):
    expected = {
        item["rfilename"]: (item.get("lfs") or {}).get("sha256")
        for item in metadata.get("siblings", [])
    }
    bad = []
    for name in names:
        path = os.path.join(dest_dir, name)
        if not os.path.exists(path):
            bad.append("%s（文件不存在）" % name)
            continue
        want = expected.get(name)
        if not want:
            print("跳过校验（该文件没有 sha256 记录）：%s" % name, flush=True)
            continue
        got = sha256_of(path)
        if got == want:
            print("校验通过：%s" % name, flush=True)
        else:
            print("校验失败：%s\n  期望 %s\n  实际 %s" % (name, want, got), flush=True)
            bad.append(name)
    return bad


def main(argv=None):
    args = parse_args(argv)
    candidates = [item.strip() for item in args.files.split(",")] if args.files else list(DEFAULT_FILES)

    metadata = repo_metadata_safe(args)
    if metadata is not None:
        available = [item["rfilename"] for item in metadata.get("siblings", [])]
        sizes = {
            item["rfilename"]: (item.get("lfs") or {}).get("size")
            for item in metadata.get("siblings", [])
        }
    else:
        available, sizes = None, {}

    if args.list_files:
        if metadata is None:
            print("仓库信息不可用，稍后重试。")
            return 1
        for item in metadata.get("siblings", []):
            lfs = item.get("lfs") or {}
            size = lfs.get("size")
            print("%s\t%s" % (item["rfilename"], "%.1f MB" % (size / 1e6) if size else ""))
        return 0

    names, missing = resolve_names(candidates, available)
    if missing:
        print("仓库里没有这些文件，已跳过：%s" % "、".join(missing), flush=True)
    if not names:
        print("没有可下载的文件，请用 --list 查看仓库内容。")
        return 1

    dest_dir = args.dest or os.path.join(os.getcwd(), os.path.basename(args.repo.rstrip("/")))
    os.makedirs(dest_dir, exist_ok=True)
    print("仓库 %s\n目录 %s\n文件 %s" % (args.repo, dest_dir, ", ".join(names)), flush=True)

    for name in names:
        fetch(args, name, dest_dir, sizes.get(name))

    if args.verify:
        if metadata is None:
            print("仓库信息不可用，无法校验 sha256。")
            return 1
        bad = verify(args, dest_dir, names, metadata)
        if bad:
            print("\n以下文件校验失败，请删除后重新下载：%s" % "、".join(bad))
            return 1

    print("\n全部完成：%s" % dest_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
