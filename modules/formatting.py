"""
TeraBox Uploader CLI: formatting.py
This module is used to format the output of the program.
It uses the colorama library to color the output.
Used in: main.py

This program is provided as-is, without any warranty.
This program is not affiliated with Terabox in any way.
This program is licensed under the MIT License.

Developed by Gonçalo M. (@dnigamer in GitHub).
For more information, please visit https://github.com/dnigamer/TeraboxUploaderCLI
If you find any bugs, please open an issue in the GitHub repository mentioned in the link above.
"""

from datetime import datetime
import os
import re
import shutil
import sys
import threading
import time

try:
    from colorama import Fore, Back, Style
except ImportError:
    class _AnsiFallback:
        def __getattr__(self, _name: str) -> str:
            return ""

    Fore = Back = Style = _AnsiFallback()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _truncate_visible(text: str, max_cols: int) -> str:
    """Truncate a string (which may contain ANSI color codes) to at most max_cols visible characters."""
    if max_cols <= 0:
        return ""
    out = []
    visible = 0
    idx = 0
    while idx < len(text):
        match = _ANSI_RE.match(text, idx)
        if match:
            out.append(match.group(0))
            idx = match.end()
            continue
        if visible >= max_cols:
            break
        out.append(text[idx])
        visible += 1
        idx += 1
    out.append(Style.RESET_ALL)
    return "".join(out)


class Formatting:
    """
    This class is used to format the output of the program.
    It uses the colorama library to color the output.
    """
    def __init__(self, timestamps=False):
        """
        This method initializes the colorama library.
        :param timestamps: If True, the output will be formatted with a timestamp.
        """
        if timestamps:
            self.timestamps = True
        else:
            self.timestamps = False
        self.fore = Fore
        self.back = Back
        self.style = Style
        self._lock = threading.Lock()
        self._progress_lines = []
        self._num_drawn_lines = 0

    def _clear_progress_locked(self) -> None:
        if self._num_drawn_lines > 0 and sys.stdout.isatty():
            sys.stdout.write(f"\x1b[{self._num_drawn_lines}A\r\x1b[J")
            self._num_drawn_lines = 0

    def _draw_progress_locked(self) -> None:
        if not self._progress_lines or not sys.stdout.isatty():
            return
        cols = max(40, shutil.get_terminal_size((100, 20)).columns - 1)
        if self._num_drawn_lines > 0:
            sys.stdout.write(f"\x1b[{self._num_drawn_lines}A\r")
        rendered = [
            f"{_truncate_visible(line, cols)}\x1b[K"
            for line in self._progress_lines
        ]
        sys.stdout.write("\n".join(rendered) + "\n")
        if len(rendered) < self._num_drawn_lines:
            sys.stdout.write("\x1b[J")
        self._num_drawn_lines = len(rendered)
        sys.stdout.flush()

    def set_progress_lines(self, lines: list) -> None:
        """Update the pinned multi-line progress block at the bottom of the terminal."""
        with self._lock:
            self._progress_lines = list(lines)
            self._draw_progress_locked()

    def clear_progress(self) -> None:
        """Clear the pinned multi-line progress block from the terminal."""
        with self._lock:
            self._clear_progress_locked()
            self._progress_lines = []
            sys.stdout.flush()

    def _print_log(self, color: str, subject: str, message: str) -> None:
        with self._lock:
            self._clear_progress_locked()
            print(
                f"{self.timestamp()}{self.style.BRIGHT}{color} {subject.upper().ljust(12)}: "
                f"{self.style.RESET_ALL}{message}",
                flush=True,
            )
            self._draw_progress_locked()

    def timestamp(self) -> str:
        """
        This method is used to format a message with a timestamp.
        :return:
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if self.timestamps else ''
        return f"{self.style.BRIGHT}[{timestamp}]{self.style.RESET_ALL}"

    def error(self, subject: str, message: str) -> None:
        """
        This method is used to format a error message.
        :param subject: Add a classification to the logged message.
        :param message: The error message.
        :return:
        """
        self._print_log(self.fore.RED, subject, message)

    def warning(self, subject: str, message: str) -> None:
        """
        This method is used to format a warning message.
        :param subject: Add a classification to the logged message.
        :param message: The warning message.
        :return:
        """
        self._print_log(self.fore.YELLOW, subject, message)

    def success(self, subject: str, message: str) -> None:
        """
        This method is used to format a success message.
        :param subject: Add a classification to the logged message.
        :param message: The success message.
        :return:
        """
        self._print_log(self.fore.GREEN, subject, message)

    def info(self, subject: str, message: str) -> None:
        """
        This method is used to format an info message.
        :param subject: Add a classification to the logged message.
        :param message: The info message.
        :return:
        """
        self._print_log(self.fore.CYAN, subject, message)

    def debug(self, subject: str, message: str) -> None:
        """
        This method is used to format a debug message.
        :param subject: Add a classification to the logged message.
        :param message: The debug message.
        :return:
        """
        self._print_log(self.fore.MAGENTA, subject, message)


def _format_bytes(size_bytes: float) -> str:
    if size_bytes <= 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    idx = 0
    val = float(size_bytes)
    while val >= 1024.0 and idx < len(units) - 1:
        val /= 1024.0
        idx += 1
    return f"{val:.2f} {units[idx]}"


def _format_bytes_short(size_bytes: float) -> str:
    if size_bytes <= 0:
        return "0"
    units = ("B", "K", "M", "G", "T")
    idx = 0
    val = float(size_bytes)
    while val >= 1024.0 and idx < len(units) - 1:
        val /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(val)}B"
    return f"{val:.1f}{units[idx]}"


def _parse_curl_size(val_str: str) -> float:
    s = val_str.strip()
    if not s:
        return 0.0
    mult = 1.0
    if s[-1] in ("k", "K"):
        mult = 1024.0
        s = s[:-1]
    elif s[-1] in ("m", "M"):
        mult = 1024.0 ** 2
        s = s[:-1]
    elif s[-1] in ("g", "G"):
        mult = 1024.0 ** 3
        s = s[:-1]
    elif s[-1] in ("t", "T"):
        mult = 1024.0 ** 4
        s = s[:-1]
    elif s[-1] in ("p", "P"):
        mult = 1024.0 ** 5
        s = s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return 0.0


def _render_bar(pct: float, width: int = 16) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = int(round((pct / 100.0) * width))
    return "█" * filled + "░" * (width - filled)


class ChunkProgressTracker:
    """Tracks multi-worker chunk upload progress and renders a live multi-line status block."""

    def __init__(
        self,
        fmt: Formatting,
        num_workers: int,
        total_chunks: int,
        total_bytes: int,
        unit_label: str = "chunks",
    ):
        self.fmt = fmt
        self.num_workers = num_workers
        self.total_chunks = total_chunks
        self.total_bytes = max(1, total_bytes)
        self.unit_label = unit_label
        self._lock = threading.Lock()
        self._free_slots = list(range(num_workers))
        self._slots = [
            {
                "active": False,
                "label": "idle",
                "pct": 0,
                "chunk_size": 0,
                "xferd": "0",
                "total": "0",
                "speed": "0",
                "speed_bps": 0.0,
                "eta": "",
                "start_time": 0.0,
                "last_update": 0.0,
            }
            for _ in range(num_workers)
        ]
        self._completed_chunks = 0
        self._completed_bytes = 0
        self._completed_time = 0.0
        self._last_render = 0.0

    def acquire_slot(self, partseq: int, local_path: str, chunk_size: int) -> int:
        base = os.path.basename(local_path)
        if ".part" in base:
            label = base.split(".")[-1]
        else:
            label = base[-7:] if len(base) > 7 else base
        now = time.monotonic()
        with self._lock:
            slot = self._free_slots.pop(0) if self._free_slots else (partseq % self.num_workers)
            self._slots[slot] = {
                "active": True,
                "base_label": label,
                "label": label,
                "pct": 0,
                "chunk_size": chunk_size,
                "xferd": "0",
                "total": _format_bytes_short(chunk_size),
                "speed": "0/s",
                "speed_bps": 0.0,
                "eta": "--:--",
                "start_time": now,
                "chunk_start_time": now,
                "prior_elapsed": 0.0,
                "attempt_elapsed": 0.0,
                "attempt": 1,
                "last_update": 0.0,
                "low_speed_since": None,
            }
            self._render_locked(force=True)
            return slot

    def reset_slot_for_retry(self, slot: int, attempt: int) -> None:
        now = time.monotonic()
        with self._lock:
            st = self._slots[slot]
            attempt_elapsed = max(
                st.get("attempt_elapsed", 0.0),
                max(0.0, now - st.get("start_time", now)),
            )
            st["prior_elapsed"] = st.get("prior_elapsed", 0.0) + attempt_elapsed
            st["attempt_elapsed"] = 0.0
            st["attempt"] = attempt
            base_label = st.get("base_label", st["label"])
            if base_label.startswith("part") and len(base_label) == 7:
                retry_label = f"p{base_label[4:]}#{attempt}"
            else:
                retry_label = f"{base_label[:5]}#{attempt}"
            st["label"] = retry_label
            st["pct"] = 0
            st["xferd"] = "0"
            st["speed"] = "0/s"
            st["speed_bps"] = 0.0
            st["eta"] = "--:--"
            st["start_time"] = now
            st["last_update"] = 0.0
            st["low_speed_since"] = None
            self._render_locked(force=True)

    def get_slot_status(self, slot: int) -> tuple:
        with self._lock:
            st = self._slots[slot]
            return st.get("speed", "0/s"), st.get("eta", "--:--"), st.get("pct", 0)

    def update_from_bytes(self, slot: int, processed_bytes: int, total_bytes: int) -> None:
        now = time.monotonic()
        st = self._slots[slot]
        if processed_bytes < total_bytes and (now - st.get("last_update", 0.0)) < 0.05:
            return
        total = max(1, total_bytes)
        pct = int((processed_bytes / total) * 100)
        elapsed = max(0.001, now - st.get("start_time", now))
        speed_bps = processed_bytes / elapsed
        rem_bytes = max(0, total - processed_bytes)
        if speed_bps > 0 and rem_bytes > 0:
            eta_sec = int(rem_bytes / speed_bps)
            eta_str = f"{eta_sec // 60:02d}:{eta_sec % 60:02d}"
        elif rem_bytes == 0:
            eta_str = "00:00"
        else:
            eta_str = "--:--"
        with self._lock:
            st = self._slots[slot]
            st["last_update"] = now
            st["pct"] = max(0, min(100, pct))
            st["xferd"] = _format_bytes_short(processed_bytes)
            st["total"] = _format_bytes_short(total)
            st["speed"] = f"{_format_bytes_short(speed_bps)}/s"
            st["eta"] = eta_str
            self._render_locked(force=False)

    def update_from_curl_line(self, slot: int, line: str) -> bool:
        tokens = line.strip().split()
        if len(tokens) < 9 or not tokens[0].isdigit():
            return False
        pct = int(tokens[4]) if tokens[4].isdigit() else int(tokens[0])
        total_str = tokens[1]
        xferd_str = tokens[5]
        cur_spd = tokens[-1]
        avg_up = tokens[7]
        eta_str = tokens[10] if len(tokens) >= 12 else (tokens[9] if len(tokens) == 11 else "--:--")
        cur_spd_bps = _parse_curl_size(cur_spd)
        avg_up_bps = _parse_curl_size(avg_up)
        now = time.monotonic()
        should_abort_slow = False
        with self._lock:
            st = self._slots[slot]
            elapsed = max(0.0, now - st.get("start_time", now))
            st["attempt_elapsed"] = elapsed
            total_elapsed = max(
                now - st.get("chunk_start_time", st.get("start_time", now)),
                st.get("prior_elapsed", 0.0) + elapsed,
            )
            prior_elapsed = max(st.get("prior_elapsed", 0.0), total_elapsed - elapsed)
            if cur_spd_bps > 0:
                speed_bps = cur_spd_bps
                speed_str = cur_spd
            elif elapsed < 5.0:
                speed_bps = avg_up_bps
                speed_str = avg_up
            else:
                speed_bps = 0.0
                speed_str = "0"
            st["pct"] = max(0, min(100, pct))
            if total_str != "0":
                st["total"] = total_str
            st["xferd"] = xferd_str
            st["speed"] = f"{speed_str}/s"
            st["speed_bps"] = speed_bps
            st["eta"] = eta_str

            completed_speed = (
                (self._completed_bytes / self._completed_time)
                if (self._completed_chunks > 0 and self._completed_time > 0)
                else 0.0
            )
            active_speeds = sorted(
                s.get("speed_bps", 0.0)
                for s in self._slots
                if s["active"] and s.get("speed_bps", 0.0) > 0
            )
            if active_speeds:
                upper_half = active_speeds[len(active_speeds) // 2 :]
                peer_speed = sum(upper_half) / len(upper_half)
            else:
                peer_speed = 0.0

            ref_speed_bps = max(completed_speed, peer_speed, avg_up_bps)
            min_speed_bps = ref_speed_bps * 0.25

            if ref_speed_bps > 0 and elapsed >= 5.0 and speed_bps < min_speed_bps:
                if st.get("low_speed_since") is None:
                    st["low_speed_since"] = now
                low_duration = now - st["low_speed_since"]
                rem_bytes = max(0.0, st["chunk_size"] * (1.0 - st["pct"] / 100.0))
                rem_eta_sec = rem_bytes / max(1.0, speed_bps)
                fresh_eta_sec = st["chunk_size"] / ref_speed_bps
                retry_eta_sec = 1.5 * fresh_eta_sec + prior_elapsed
                if (
                    low_duration >= 6.0
                    and rem_eta_sec > retry_eta_sec
                    and rem_eta_sec > total_elapsed
                ):
                    should_abort_slow = True
            elif ref_speed_bps > 0 and speed_bps >= min_speed_bps:
                st["low_speed_since"] = None

            self._render_locked(force=False)
        return should_abort_slow

    def release_slot(self, slot: int, success: bool) -> None:
        now = time.monotonic()
        with self._lock:
            st = self._slots[slot]
            if success:
                self._completed_chunks += 1
                self._completed_bytes += st["chunk_size"]
                self._completed_time += max(0.1, now - st.get("start_time", now))
            self._slots[slot] = {
                "active": False,
                "label": "idle",
                "pct": 0,
                "chunk_size": 0,
                "xferd": "0",
                "total": "0",
                "speed": "0",
                "speed_bps": 0.0,
                "eta": "",
            }
            if slot not in self._free_slots:
                self._free_slots.append(slot)
                self._free_slots.sort()
            self._render_locked(force=True)

    def close(self) -> None:
        self.fmt.clear_progress()

    def _render_locked(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._last_render) < 0.03:
            return
        self._last_render = now

        lines = []
        in_flight_bytes = 0.0
        for idx, st in enumerate(self._slots):
            prefix = f"  {Style.BRIGHT}{Fore.CYAN}[W{idx + 1}]{Style.RESET_ALL}"
            if st["active"]:
                in_flight_bytes += (st["pct"] / 100.0) * st["chunk_size"]
                bar = _render_bar(st["pct"], width=16)
                lines.append(
                    f"{prefix} {st['label']:<7} [{Fore.GREEN}{bar}{Style.RESET_ALL}] "
                    f"{st['pct']:3d}% | {st['xferd']:>6}/{st['total']:<6} | "
                    f"{st['speed']:>8} | ETA {st['eta']}"
                )
            else:
                lines.append(f"{prefix} {Style.DIM}idle{Style.RESET_ALL}")

        current_bytes = min(self.total_bytes, self._completed_bytes + in_flight_bytes)
        overall_pct = (current_bytes / self.total_bytes) * 100.0
        overall_bar = _render_bar(overall_pct, width=16)
        lines.append(
            f"  {Style.BRIGHT}{Fore.YELLOW}[All]{Style.RESET_ALL} "
            f"{self._completed_chunks}/{self.total_chunks} {self.unit_label} "
            f"[{Fore.YELLOW}{overall_bar}{Style.RESET_ALL}] {overall_pct:5.1f}% "
            f"({_format_bytes(current_bytes)} / {_format_bytes(self.total_bytes)})"
        )
        self.fmt.set_progress_lines(lines)

