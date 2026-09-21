#!/usr/bin/env python3
"""用 faster-whisper 转写录音，输出带时间点的文字稿和结构化 JSON。

用法：
    python transcribe.py 录音.m4a --model ./models/large-v3 --language zh --prompt "简体中文会议记录"

依赖：faster-whisper（自带 PyAV 解码，不需要系统 ffmpeg）。
"""

import argparse
import json
import os
import sys
import time


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("audio", help="音频或视频文件")
    parser.add_argument(
        "--model",
        default="Systran/faster-whisper-large-v3",
        help="本地模型目录，或 Hugging Face 模型名（默认 large-v3）",
    )
    parser.add_argument("--out", help="结构化 JSON 路径，默认与音频同名加 .transcript.json")
    parser.add_argument("--txt", help="纯文字稿路径，默认与 --out 同名加 .txt")
    parser.add_argument("--language", default=None, help="语言代码，如 zh；不填则自动判断")
    parser.add_argument(
        "--prompt",
        default=None,
        help="初始提示词，例如「简体中文会议记录，保留专有名词、人名、数字与日期」",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--threads", type=int, default=0, help="CPU 线程数，0 表示用满所有核心")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--no-vad", action="store_true", help="关闭 VAD 静音过滤（默认开启）")
    parser.add_argument(
        "--low-logprob",
        type=float,
        default=-1.0,
        help="平均对数概率低于该值的段落列为需要复核",
    )
    return parser.parse_args(argv)


def format_timestamp(seconds):
    seconds = max(0.0, float(seconds))
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return "%02d:%02d:%02d" % (hours, minutes, secs)


def output_paths(audio, out, txt):
    base = os.path.splitext(os.path.abspath(audio))[0]
    out = out or base + ".transcript.json"
    txt = txt or os.path.splitext(out)[0] + ".txt"
    return out, txt


def main(argv=None):
    args = parse_args(argv)

    if not os.path.exists(args.audio):
        sys.exit("找不到音频文件：%s" % args.audio)

    from faster_whisper import WhisperModel

    out_path, txt_path = output_paths(args.audio, args.out, args.txt)
    jsonl_path = os.path.splitext(out_path)[0] + ".jsonl"
    threads = args.threads or (os.cpu_count() or 4)

    print(
        "加载模型 %s（device=%s, compute_type=%s, threads=%d）"
        % (args.model, args.device, args.compute_type, threads),
        flush=True,
    )
    started = time.time()
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        cpu_threads=threads,
    )
    print("模型就绪，用时 %.1fs" % (time.time() - started), flush=True)

    segments, info = model.transcribe(
        args.audio,
        language=args.language,
        beam_size=args.beam_size,
        initial_prompt=args.prompt,
        vad_filter=not args.no_vad,
        vad_parameters={"min_silence_duration_ms": 400},
        condition_on_previous_text=False,
    )
    print(
        "识别语言 %s（置信度 %.2f），音频时长 %.1f 秒"
        % (info.language, info.language_probability, info.duration),
        flush=True,
    )

    results = []
    flagged = []
    with open(jsonl_path, "w", encoding="utf-8") as stream:
        for segment in segments:
            text = (segment.text or "").strip()
            item = {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text,
                "avg_logprob": round(segment.avg_logprob, 3),
                "no_speech_prob": round(segment.no_speech_prob, 3),
            }
            results.append(item)
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")
            stream.flush()
            if not text or item["avg_logprob"] < args.low_logprob:
                flagged.append(item)
            print("[%s] %s" % (format_timestamp(segment.start), text), flush=True)

    payload = {
        "audio": os.path.abspath(args.audio),
        "model": args.model,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration": round(info.duration, 2),
        "segments": results,
    }
    with open(out_path, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=1)
    with open(txt_path, "w", encoding="utf-8") as stream:
        for item in results:
            if not item["text"]:
                continue
            stream.write("[%s] %s\n" % (format_timestamp(item["start"]), item["text"]))

    print("\n共 %d 段，总用时 %.1fs" % (len(results), time.time() - started))
    print("结构化结果：%s" % out_path)
    print("文字稿：%s" % txt_path)
    print("中间结果：%s" % jsonl_path)

    if flagged:
        print("\n需要复核的段落（空文本或平均对数概率低于 %.2f）：" % args.low_logprob)
        for item in flagged:
            print("  [%s] %s" % (format_timestamp(item["start"]), item["text"] or "<空>"))
    else:
        print("\n没有低置信度段落，仍建议抽查人名、数字和决定事项。")


if __name__ == "__main__":
    main()
