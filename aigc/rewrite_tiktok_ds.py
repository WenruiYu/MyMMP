# -*- coding: utf-8 -*-
"""
Rewrite TikTok scripts via DeepSeek Platform API (OpenAI-compatible).
- Preserves languages per side (no translation): TTS keeps TTS languages; Caption keeps Caption languages.
- TTS outputs -> folder of --tts; Caption outputs -> folder of --caption.
- Streaming with compact mode; robust JSON parsing; supports N variants per request.
"""

import os, re, json, time, argparse, sys
from pathlib import Path
from typing import List, Tuple, Dict, Any
from openai import OpenAI

HASHTAG_PATTERN = re.compile(r"#([\w\-\u4e00-\u9fff]+)", re.UNICODE)

def preprocess_tts_text(text):
    """
    Preprocess TTS text by converting all punctuation marks to newlines.
    This is necessary because batch-generated TTS documents currently cannot handle automatic line breaks.
    """
    if not text:
        return text
    
    # Define all common punctuation marks including Chinese and English punctuation
    # Using a single string to avoid any spacing issues
    punctuation_marks = (
        '，。！？；：、'  # Chinese punctuation
        ',.!?;:'  # English punctuation  
        '-—…~～'  # Dashes and ellipsis
        '（）()'  # Parentheses
        '[]【】'  # Brackets
        '《》〈〉'  # Angle brackets
        '「」『』'  # Japanese quotes
        '""'''  # Smart quotes
        '"'  # Regular double quotes (removed single quote to preserve contractions/possessives)
        '`/|\\'  # Other marks
    )
    
    # Create pattern - escape special regex characters
    punctuation_pattern = '[' + re.escape(punctuation_marks) + ']'
    
    # Replace all punctuation marks with newlines
    processed_text = re.sub(punctuation_pattern, '\n', text)
    
    # Split into lines and clean each line
    lines = processed_text.split('\n')
    # Remove empty lines and strip whitespace from each line
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    
    # Join back with newlines
    processed_text = '\n'.join(cleaned_lines)
    
    return processed_text

# ---------- IO helpers ----------

def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read().strip()

def split_caption_and_tags(caption: str) -> Tuple[str, List[str]]:
    tags = [f"#{m.group(1)}" for m in HASHTAG_PATTERN.finditer(caption)]
    body = HASHTAG_PATTERN.sub("", caption)
    body = re.sub(r"\s{2,}", " ", body).strip()
    return body, tags

def style_preset(i: int) -> str:
    presets = [
        "钩子=反问句；语气=口语化；句长=短；节奏=快；",
        "钩子=数字开头；语气=热情；句长=短；节奏=中；",
        "钩子=悬念；语气=平实可信；句长=中；节奏=慢；",
        "钩子=对比；语气=好奇探索；句长=短；节奏=快；",
        "钩子=命令式；语气=直接有力；句长=短；节奏=快；",
    ]
    return presets[i % len(presets)]

# ---------- Light language fingerprint (for model hint) ----------

def lang_signature(text: str) -> str:
    sig = []
    if re.search(r"[\u4e00-\u9fff]", text): sig.append("Chinese")
    if re.search(r"[A-Za-z]", text): sig.append("Latin")
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text): sig.append("Japanese")
    if re.search(r"[\uac00-\ud7af]", text): sig.append("Korean")
    if re.search(r"[\u0e00-\u0e7f]", text): sig.append("Thai")
    if re.search(r"[\u0400-\u04FF]", text): sig.append("Cyrillic")
    if re.search(r"[\u0600-\u06FF]", text): sig.append("Arabic")
    if re.search(r"[0-9]", text): sig.append("Digits")
    if re.search(r"[\U0001F300-\U0001FAFF]", text): sig.append("Emoji")
    return ", ".join(sig) if sig else "Unknown"

# ---------- JSON sanitization ----------

def strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.DOTALL)
    # Also clean up any trailing spaces on each line which can cause JSON parsing issues
    lines = s.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    s = '\n'.join(cleaned_lines)
    return s

def normalize_quotes(s: str) -> str:
    # Don't normalize quotes that are inside JSON string values
    # Only normalize smart quotes to regular quotes, but leave Chinese quotes as-is
    # since they don't conflict with JSON syntax
    s = s.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
    # Don't replace Chinese quotation marks as they're valid inside JSON strings
    # s = s.replace(""", '"').replace(""", '"')  # Commented out - keep Chinese quotes
    return s

def escape_newlines_in_strings(s: str) -> str:
    out, in_str, esc = [], False, False
    for ch in s:
        if in_str:
            if esc: out.append(ch); esc = False
            else:
                if ch == "\\": out.append(ch); esc = True
                elif ch == '"': out.append(ch); in_str = False
                elif ch in ("\n", "\r"): out.append("\\n")
                else: out.append(ch)
        else:
            if ch == '"': out.append(ch); in_str = True; esc = False
            else: out.append(ch)
    return "".join(out)

def trim_to_complete_json(s: str) -> str:
    # Keep up to last complete {...} or [...] at top level
    depth_obj = depth_arr = 0
    last_complete = -1
    in_str = False; esc = False
    for i, ch in enumerate(s):
        if in_str:
            if esc: esc = False
            else:
                if ch == "\\": esc = True
                elif ch == '"': in_str = False
        else:
            if ch == '"': in_str = True
            elif ch == "{": depth_obj += 1
            elif ch == "}":
                depth_obj -= 1
                if depth_obj == 0 and depth_arr == 0: last_complete = i
            elif ch == "[": depth_arr += 1
            elif ch == "]":
                depth_arr -= 1
                if depth_arr == 0 and depth_obj == 0: last_complete = i
    return s[: last_complete + 1] if last_complete != -1 else s

def robust_parse_json(raw: str) -> Any:
    s = strip_code_fences(raw)
    s = normalize_quotes(s)
    s = escape_newlines_in_strings(s)
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        # Try trimming to complete JSON
        try:
            s2 = trim_to_complete_json(s)
            return json.loads(s2)
        except Exception:
            # If still failing, try one more time with aggressive cleaning
            # Remove any trailing content after the last }
            last_brace = s.rfind('}')
            if last_brace != -1:
                s3 = s[:last_brace + 1]
                try:
                    return json.loads(s3)
                except Exception:
                    pass
            raise e

# ---------- Streaming printer ----------

class StreamPrinter:
    def __init__(self, mode: str = "compact", logfile: Path | None = None):
        self.mode = mode
        self.buf = []
        self.last_flush = time.time()
        self.logfile = logfile
        if logfile:
            logfile.parent.mkdir(parents=True, exist_ok=True)
            logfile.write_text("", encoding="utf-8")

    def _write_log(self, text: str):
        if self.logfile:
            with self.logfile.open("a", encoding="utf-8") as f:
                f.write(text)

    def add(self, text: str):
        if not text:
            return
        self._write_log(text)
        if self.mode == "raw":
            sys.stdout.write(text); sys.stdout.flush()
            return
        # compact: collapse whitespace & flush in chunks
        self.buf.append(text)
        now = time.time()
        if (now - self.last_flush) > 0.05 or len("".join(self.buf)) > 400:
            chunk = "".join(self.buf)
            chunk = re.sub(r"[ \t\r\n]+", " ", chunk)
            sys.stdout.write(chunk); sys.stdout.flush()
            self.buf = []
            self.last_flush = now

    def close(self):
        if self.buf:
            chunk = "".join(self.buf)
            chunk = re.sub(r"[ \t\r\n]+", " ", chunk)
            sys.stdout.write(chunk); sys.stdout.flush()
            self.buf = []

# ---------- API wrappers ----------

def call_stream(client: OpenAI, model: str, system_prompt: str, user_prompt: str,
                show_reasoning: bool, max_tokens: int, temperature: float,
                stream_style: str, stream_log: Path | None) -> str:
    print("\n===== streaming started =====", flush=True)
    if model == "deepseek-reasoner" and show_reasoning:
        print("----- reasoning (live) -----", flush=True)
    else:
        print("----- content (live) -----", flush=True)

    content_buf: List[str] = []
    sp = StreamPrinter(mode=stream_style, logfile=stream_log)

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":system_prompt}, {"role":"user","content":user_prompt}],
        response_format={"type":"json_object"},
        stream=True,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        rc = getattr(delta, "reasoning_content", None)
        if rc and show_reasoning:
            sp.add(rc)
        part = getattr(delta, "content", None)
        if part:
            sp.add(part)
            content_buf.append(part)

    sp.close()
    print("\n===== streaming done =====\n", flush=True)
    return "".join(x for x in content_buf if x)

def call_no_stream(client: OpenAI, model: str, system_prompt: str, user_prompt: str,
                   max_tokens: int, temperature: float) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":system_prompt}, {"role":"user","content":user_prompt}],
        response_format={"type":"json_object"},
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""

# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser(description="Rewrite TikTok scripts - supports both TTS+Caption and Caption-only modes")
    ap.add_argument("--tts", required=False, help="TTS file path (optional - omit for caption-only mode)")
    ap.add_argument("--caption", required=True, help="Caption file path (required)")
    ap.add_argument("-n","--num", type=int, default=3, help="Total variants to generate")
    ap.add_argument("--variants-per-request", type=int, default=1, help="How many variants per API request")
    ap.add_argument("--model", default="deepseek-chat")
    ap.add_argument("--base_url", default="https://api.deepseek.com")
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--stream", action="store_true")
    ap.add_argument("--no-reasoning", action="store_true")
    ap.add_argument("--stream-style", choices=["raw","compact"], default="compact")
    ap.add_argument("--stream-log", default=None, help="Optional path to save full stream (reasoning+content)")
    ap.add_argument("--max_tokens", type=int, default=3072)
    ap.add_argument("--retries", type=int, default=2, help="Retries on malformed JSON")
    ap.add_argument("--no-tts", action="store_true", help="Caption-only mode - skip TTS generation, only process captions")
    args = ap.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置环境变量 DEEPSEEK_API_KEY")

    client = OpenAI(api_key=api_key, base_url=args.base_url)

    cap_path = Path(args.caption).resolve()
    cap_dir = cap_path.parent

    cap_src = read_text(cap_path)
    cap_body, tags = split_caption_and_tags(cap_src)
    cap_sig = lang_signature(cap_body)

    # Handle TTS if provided
    tts_src = None
    tts_sig = None
    tts_dir = None
    if args.tts and not args.no_tts:
        tts_path = Path(args.tts).resolve()
        tts_dir = tts_path.parent
        tts_src = read_text(tts_path)
        tts_sig = lang_signature(tts_src)

    # Build prompts
    if tts_src:
        language_rules = (
            "• 语言保持：TTS 仅按 TTS 原文的语言/混合语言改写；Caption 仅按 Caption 正文的语言/混合语言改写；"
            "禁止翻译或跨语言替换；保持原有 code-switching 位置与比例；品牌/地名/人名/型号/数字/货币符号/Emoji 原样保留。"
        )
        base_rules = (
            "• TTS：口语化、易念，长度与原稿接近（±20%）；避免拗口与过长句。\n"
            "• Caption：首句做强钩子（中文≤10字；英文≤6 words），不得新增标签；不得在正文中出现#标签。\n"
            "• 只输出合法 JSON。"
        )
    else:
        language_rules = (
            "• 语言保持：Caption 仅按 Caption 正文的语言/混合语言改写；"
            "禁止翻译或跨语言替换；保持原有 code-switching 位置与比例；品牌/地名/人名/型号/数字/货币符号/Emoji 原样保留。"
        )
        base_rules = (
            "• Caption：首句做强钩子（中文≤10字；英文≤6 words），不得新增标签；不得在正文中出现#标签。\n"
            "• 只输出合法 JSON。"
        )

    def build_user_prompt(batch_index: int, expect_k: int) -> str:
        # If expect_k == 1, single object; else variants array with exact length
        if tts_src:
            template_single = "{\n  \"tts\": \"改写后的 TTS 文案（保持原语言/混合语言，不翻译）\",\n  \"caption\": \"改写后的下方文案（保持原语言/混合语言，不翻译；不含任何标签）\"\n}"
            template_multi = "{\n  \"variants\": [\n    {\"tts\": \"...\", \"caption\": \"...\"}\n  ]\n}"
            
            return (
                (f"【任务】此轮生成 {expect_k} 个互不重复的变体；"
                 f"{'直接返回单个JSON对象' if expect_k==1 else '返回一个包含 variants 数组的 JSON 对象，variants 长度必须精确等于 '+str(expect_k)}；"
                 "不得返回除 JSON 以外的任何文本。\n") +
                f"【风格提示】{style_preset(batch_index)}\n"
                f"【TTS 语言指纹】{tts_sig}\n"
                f"【Caption 语言指纹】{cap_sig}\n\n"
                "【TTS 原文】\n" + tts_src + "\n\n" +
                "【下方文案正文（不含标签）】\n" + cap_body + "\n\n" +
                "【输出 JSON 模板】\n" + (template_single if expect_k==1 else template_multi) + "\n"
            )
        else:
            template_single = "{\n  \"caption\": \"改写后的下方文案（保持原语言/混合语言，不翻译；不含任何标签）\"\n}"
            template_multi = "{\n  \"variants\": [\n    {\"caption\": \"...\"}\n  ]\n}"
            
            return (
                (f"【任务】此轮生成 {expect_k} 个互不重复的 Caption 变体；"
                 f"{'直接返回单个JSON对象' if expect_k==1 else '返回一个包含 variants 数组的 JSON 对象，variants 长度必须精确等于 '+str(expect_k)}；"
                 "不得返回除 JSON 以外的任何文本。\n") +
                f"【风格提示】{style_preset(batch_index)}\n"
                f"【Caption 语言指纹】{cap_sig}\n\n"
                "【下方文案正文（不含标签）】\n" + cap_body + "\n\n" +
                "【输出 JSON 模板】\n" + (template_single if expect_k==1 else template_multi) + "\n"
            )

    # System prompt varies with per-request setting and TTS availability
    if tts_src:
        system_prompt_single = (
            "你是短视频文案改写助手。严格输出 json（单个对象，不得包含数组或 variants 键）。结构：{\"tts\":\"...\",\"caption\":\"...\"}。\n"
            + language_rules + "\n" + base_rules
        )
        system_prompt_multi = (
            "你是短视频文案改写助手。严格输出 json（对象内包含 variants 数组）。结构：{\"variants\":[{\"tts\":\"...\",\"caption\":\"...\"}, ...]}。\n"
            "variants 的长度必须与指令一致，不得多也不得少。\n"
            + language_rules + "\n" + base_rules
        )
    else:
        system_prompt_single = (
            "你是短视频文案改写助手。严格输出 json（单个对象，不得包含数组或 variants 键）。结构：{\"caption\":\"...\"}。\n"
            + language_rules + "\n" + base_rules
        )
        system_prompt_multi = (
            "你是短视频文案改写助手。严格输出 json（对象内包含 variants 数组）。结构：{\"variants\":[{\"caption\":\"...\"}, ...]}。\n"
            "variants 的长度必须与指令一致，不得多也不得少。\n"
            + language_rules + "\n" + base_rules
        )

    total_needed = args.num
    per_req = max(1, args.variants_per_request)
    made = 0
    batch_index = 0
    global_variant_index = 0

    while made < total_needed:
        k = min(per_req, total_needed - made)  # last batch may be smaller
        batch_index += 1
        
        # Debug output
        print(f"\n[Debug] Batch {batch_index}: made={made}, total_needed={total_needed}, k={k}")

        system_prompt = system_prompt_multi if k > 1 else system_prompt_single
        user_prompt = build_user_prompt(batch_index-1, k)

        # call with retries
        raw = ""
        for attempt in range(args.retries + 1):
            try:
                if args.stream:
                    stream_log = Path(args.stream_log) if args.stream_log else None
                    raw = call_stream(
                        client, args.model, system_prompt, user_prompt,
                        show_reasoning=(not args.no_reasoning),
                        max_tokens=args.max_tokens,
                        temperature=args.temperature,
                        stream_style=args.stream_style,
                        stream_log=stream_log
                    )
                else:
                    raw = call_no_stream(
                        client, args.model, system_prompt, user_prompt,
                        max_tokens=args.max_tokens, temperature=args.temperature
                    )

                if not raw.strip():
                    raise RuntimeError("空响应")
                data = robust_parse_json(raw)
                break
            except Exception as e:
                if attempt >= args.retries:
                    raise RuntimeError(f"解析失败（已重试 {args.retries} 次）。原始片段：{raw[:800]}") from e
                time.sleep(1.2 * (attempt + 1))

        # normalize to variants list
        variants: List[Dict[str, str]] = []
        if k == 1:
            if isinstance(data, dict) and ("tts" in data or "caption" in data):
                variants = [data]
            elif isinstance(data, dict) and "variants" in data and isinstance(data["variants"], list) and len(data["variants"]) >= 1:
                variants = data["variants"][:1]
            else:
                raise RuntimeError(f"JSON 结构不符合单对象要求：{data}")
        else:
            if not (isinstance(data, dict) and isinstance(data.get("variants"), list)):
                raise RuntimeError(f"JSON 结构应包含 variants 数组：{data}")
            if len(data["variants"]) != k:
                # tolerate overlong by trimming, or underlong by error
                if len(data["variants"]) > k:
                    variants = data["variants"][:k]
                else:
                    raise RuntimeError(f"variants 长度不符，期望 {k}，实际 {len(data['variants'])}")
            else:
                variants = data["variants"]

        # write files
        print(f"\n[Debug] Writing {len(variants)} variants...")
        for item in variants:
            global_variant_index += 1
            
            # Handle TTS output if TTS is provided
            if tts_src and tts_dir:
                tts_out = (item.get("tts") or "").strip()
                # Preprocess TTS text to convert punctuation to newlines
                tts_out = preprocess_tts_text(tts_out)
                idx = f"{global_variant_index:02d}"
                (tts_dir / f"variant_{idx}_tts.txt").write_text(tts_out, encoding="utf-8")
                print(f"✓ TTS: {tts_dir / f'variant_{idx}_tts.txt'}")
            
            # Always handle caption output
            cap_out = (item.get("caption") or "").strip()
            if tags:
                cap_out = (cap_out + "\n" + " ".join(tags)).strip()

            idx = f"{global_variant_index:02d}"
            (cap_dir / f"variant_{idx}_caption.txt").write_text(cap_out, encoding="utf-8")
            print(f"✓ Caption: {cap_dir / f'variant_{idx}_caption.txt'}")

        made += len(variants)
        print(f"[Debug] Total made so far: {made}")

if __name__ == "__main__":
    main()
