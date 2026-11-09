SORT_WHITELIST = {"vod_time", "vod_score", "vod_id"}


class VodService:
    @staticmethod
    def get_list(cur, params: dict):
        page = params["page"]
        size = params["size"]
        pid = params.get("pid")
        typ = params.get("type")
        year = params.get("year")
        area = params.get("area")
        lang = params.get("lang")
        cls = params.get("class")
        sort = params.get("sort", "vod_time")
        order = params.get("order", "DESC")

        if order.upper() not in ("ASC", "DESC"):
            order = "DESC"
        if sort not in SORT_WHITELIST:
            sort = "vod_time"

        where_parts = []
        args = []
        if pid:
            where_parts.append("type_id = %s")
            args.append(pid)
        if typ:
            where_parts.append("type_id_1 = %s")
            args.append(typ)
        if year:
            where_parts.append("vod_year = %s")
            args.append(year)
        if area:
            where_parts.append("vod_area = %s")
            args.append(area)
        if lang:
            where_parts.append("vod_lang = %s")
            args.append(lang)
        if cls:
            where_parts.append("vod_class = %s")
            args.append(cls)

        where_sql = " AND ".join(where_parts)
        if where_sql:
            where_sql = "WHERE " + where_sql

        count_sql = f"SELECT COUNT(*) AS cnt FROM vod {where_sql}"
        cur.execute(count_sql, args)
        total = cur.fetchone()["cnt"]

        list_sql = f"""
            SELECT vod_id,type_id,type_name,vod_name,vod_sub,vod_class,vod_pic,
                   vod_actor,vod_director,vod_time,vod_area,vod_lang,vod_year,
                   vod_remarks,vod_score,vod_content
            FROM vod
            {where_sql}
            ORDER BY {sort} {order}
            LIMIT %s OFFSET %s
        """
        cur.execute(list_sql, args + [size, (page - 1) * size])
        rows = cur.fetchall()

        return {
            "list": rows,
            "total": total,
            "page": page,
            "limit": size
        }

    @staticmethod
    def get_detail(cur, vid: int):
        sql = """
            SELECT vod_id,type_id,type_name,vod_name,vod_sub,vod_class,vod_pic,
                   vod_actor,vod_director,vod_time,vod_area,vod_lang,vod_year,
                   vod_remarks,vod_score,vod_content
            FROM vod WHERE vod_id = %s
        """
        cur.execute(sql, [vid])
        return cur.fetchone()


    @staticmethod
    def search(cur, keyword: str, year: str, page: int, size: int):
        import re
        # 判断是否包含汉字
        has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', keyword))
        args = []
        if has_chinese:
            # 含汉字：多字段模糊匹配 %keyword%
            args.append(f"%{keyword}%")
            base_where = "(vod_name ILIKE %s OR vod_actor ILIKE %s OR vod_director ILIKE %s)"
            # 注意：三个位置都用同一个值，所以args追加3次
            args.append(f"%{keyword}%")
            args.append(f"%{keyword}%")
        else:
            # 无汉字：前缀匹配 keyword%
            args.append(f"{keyword}%")
            base_where = "(vod_name ILIKE %s OR vod_name_letter ILIKE %s)"
            args.append(f"{keyword}%")

        where_sql = f"WHERE {base_where}"

        # 年份条件
        if year and year.strip():
            year_val = year.strip()
            where_sql += " AND vod_year = %s"
            args.append(year_val)

        # 统计总数
        count_sql = f"SELECT COUNT(*) AS cnt FROM vod {where_sql}"
        cur.execute(count_sql, args)
        total = cur.fetchone()["cnt"]

        # 列表查询
        list_sql = f"""
            SELECT vod_id,type_id,type_name,vod_name,vod_sub,vod_class,vod_pic,
                   vod_actor,vod_director,vod_time,vod_area,vod_lang,vod_year,
                   vod_remarks,vod_score,vod_content
            FROM vod
            {where_sql}
            ORDER BY vod_time DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(list_sql, args + [size, (page - 1) * size])
        rows = cur.fetchall()
        return {"list": rows, "total": total, "page": page, "limit": size}


    @staticmethod
    def get_categories(cur):
        sql = """
                SELECT type_id, type_name, type_pid
                FROM category
                ORDER BY type_pid, type_id
            """
        cur.execute(sql)
        return cur.fetchall()


    @staticmethod
    def build_category_tree(cur):
        sql = """
                SELECT type_id, type_pid, type_name
                FROM category
                ORDER BY type_pid, type_id
            """
        cur.execute(sql)
        rows = cur.fetchall()

        def build(items, parent_id=0):
            res = []
            for item in items:
                if item["type_pid"] == parent_id:
                    children = build(items, item["type_id"])
                    res.append({**item, "children": children})
            return res

        return build(rows)


    @staticmethod
    def get_parent_categories(cur):
        sql = """
                SELECT type_id, type_pid, type_name
                FROM category
                WHERE type_pid = 0
                ORDER BY type_id
            """
        cur.execute(sql)
        return cur.fetchall()


    @staticmethod
    def get_children_categories(cur, pid: int):
        sql = """
                SELECT type_id, type_pid, type_name
                FROM category
                WHERE type_pid = %s
                ORDER BY type_id
            """
        cur.execute(sql, [pid])
        return cur.fetchall()


    @staticmethod
    def get_rank(cur, limit: int):
        sql = """
                SELECT vod_id,type_id,type_name,vod_name,vod_sub,vod_class,vod_pic,
                       vod_actor,vod_director,vod_time,vod_area,vod_lang,vod_year,
                       vod_remarks,vod_score,vod_content
                FROM vod
                WHERE type_id_1=1
                  AND vod_score ~ '^[0-9.]+$'
                  AND vod_score::DECIMAL >= 5.0
                ORDER BY vod_score::DECIMAL DESC
                LIMIT %s
            """
        cur.execute(sql, [limit])
        return cur.fetchall()


    @staticmethod
    def get_relate(cur, type_id: int, exclude_id: int, limit: int):
        sql = """
                SELECT vod_id,type_id,type_name,vod_name,vod_sub,vod_class,vod_pic,
                       vod_actor,vod_director,vod_time,vod_area,vod_lang,vod_year,
                       vod_remarks,vod_score,vod_content
                FROM vod
                WHERE type_id = %s AND vod_id != %s
                ORDER BY vod_time DESC
                LIMIT %s
            """
        cur.execute(sql, [type_id, exclude_id, limit])
        return cur.fetchall()


    @staticmethod
    def get_stats(cur):
        sql = """
                SELECT
                  COUNT(*) as total,
                  COUNT(DISTINCT type_id) as type_count,
                  COUNT(DISTINCT vod_year) as year_count,
                  COUNT(DISTINCT vod_area) as area_count,
                  AVG(CAST(vod_score AS FLOAT)) as avg_score
                FROM vod
                WHERE vod_score IS NOT NULL AND vod_score != ''
            """
        cur.execute(sql)
        return cur.fetchone()


    @staticmethod
    def get_years(cur):
        sql = """
                SELECT vod_year, COUNT(*) as count
                FROM vod
                WHERE vod_year IS NOT NULL AND vod_year != ''
                GROUP BY vod_year
                ORDER BY vod_year DESC
            """
        cur.execute(sql)
        return cur.fetchall()


    @staticmethod
    def get_areas(cur):
        sql = """
                SELECT vod_area, COUNT(*) as count
                FROM vod
                WHERE vod_area IS NOT NULL AND vod_area != ''
                GROUP BY vod_area
                ORDER BY count DESC
            """
        cur.execute(sql)
        return cur.fetchall()


    @staticmethod
    def batch_get(cur, ids: list[int]):
        placeholders = ",".join(["%s"] * len(ids))
        sql = f"""
                SELECT vod_id,type_id,type_name,vod_name,vod_sub,vod_class,vod_pic,
                       vod_actor,vod_director,vod_time,vod_area,vod_lang,vod_year,
                       vod_remarks,vod_score,vod_content
                FROM vod
                WHERE vod_id IN ({placeholders})
            """
        cur.execute(sql, ids)
        return cur.fetchall()
