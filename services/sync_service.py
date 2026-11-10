import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import requests
from pypinyin import lazy_pinyin, Style
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from db import with_db


class SyncService:
    KEEP_FIELDS = [
        "vod_id", "type_id", "type_name", "type_id_1",
        "vod_name", "vod_sub", "vod_en", "vod_letter",
        "vod_class", "vod_pic", "vod_actor", "vod_director",
        "vod_area", "vod_lang", "vod_year", "vod_douban_id",
        "vod_douban_score", "vod_content", "vod_remarks",
        "vod_score", "vod_play_url", "vod_status", "vod_time",
        "vod_name_letter"
    ]

    def __init__(self, api_base_url: str, table_name: str, max_thread: int):
        self.API_BASE_URL = api_base_url
        self.TABLE_NAME = table_name
        self.MAX_THREAD = max_thread

        self.progress_lock = Lock()
        self.is_running = False
        self.completed = 0
        self.total_pages = 1

    @staticmethod
    def get_chinese_first_letter(text: str) -> str:
        if not text:
            return ""
        result = []
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                pinyin_list = lazy_pinyin(char, style=Style.FIRST_LETTER)
                if pinyin_list:
                    first_letter = pinyin_list[0].upper()
                    if first_letter.isalpha():
                        result.append(first_letter)
            else:
                if char.isalpha():
                    result.append(char.upper())
                elif char.isdigit():
                    result.append(char)
            if len(result) >= 50:
                break
        return ''.join(result[:50])

    @staticmethod
    def get_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(total=5, backoff_factor=1, allowed_methods=["GET"])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def clean_field(val):
        if not val:
            return ""
        return val.split("$$$")[-1] if "$$$" in val else val

    def clean_video_data(self, v: dict) -> dict:
        cleaned = {}
        for k in self.KEEP_FIELDS:
            if k == "vod_name_letter":
                vod_name = v.get("vod_name", "")
                cleaned[k] = self.get_chinese_first_letter(vod_name)
            else:
                value = v.get(k, "")
                if k == "vod_play_url":
                    value = self.clean_field(value)
                cleaned[k] = value
        return cleaned

    def save_single_page(self, videos: list[dict]):
        if not videos:
            return

        def _insert(cur, conn):
            for v in videos:
                v = self.clean_video_data(v)
                cols = list(v.keys())
                vals = list(v.values())
                placeholders = ",".join(["%s"] * len(vals))
                updates = ",".join([f"{c}=%s" for c in cols])
                sql = f"""
                INSERT INTO {self.TABLE_NAME} ({','.join(cols)})
                VALUES ({placeholders})
                ON CONFLICT (vod_id) DO UPDATE SET {updates}
                """
                cur.execute(sql, vals + vals)

        with_db(_insert)


    def get_detail_by_page(self, page: int) -> list[dict]:
        try:
            resp = self.get_session().get(f"{self.API_BASE_URL}?pg={page}&ac=detail&h=24", timeout=15)
            if (page == 1):
                self.total_pages = int(resp.json().get("pagecount", 1))
            return resp.json().get("list", [])
        except Exception as e:
            print(f"page {page} get ids error:", e)
            return []

    def task(self, page: int):
        try:
            time.sleep(1.3)
            details = self.get_detail_by_page(page)
            self.save_single_page(details)
        finally:
            with self.progress_lock:
                self.completed += 1
                print(f"📊 进度：{self.completed}/{self.total_pages} | 第 {page} 页 ✅")
    def sync_start(self):
        """执行一步：只处理 current_page，处理完+1，到末尾自动停止"""
        with self.progress_lock:
            if self.is_running:
                return
            self.is_running = True
            self.total_pages = 1
            self.completed = 0
        print(f"🚀 开始同步")
        for page in range(1, 10 + 1):
            if (page <= self.total_pages and self.is_running):
                self.task(page)
        print("\n🎉 同步完成！")
        with self.progress_lock:
            self.is_running = False

    def get_sync_status(self) -> dict:
        with self.progress_lock:
            return {
                "is_running": self.is_running,
                "completed": self.completed,
                "total_pages": self.total_pages
            }

    def mark_sync_stop(self):
        with self.progress_lock:
            self.is_running = False
