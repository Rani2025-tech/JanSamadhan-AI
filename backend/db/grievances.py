import os
import uuid
from typing import Optional
from datetime import datetime, timedelta
import bcrypt
from backend.db.database import get_conn, _exec, _ph, _row_to_dict

SLA_HOURS = {
    "Critical": 24,
    "High": 48,
    "Medium": 168,
    "Low": 360
}

def init_grievance_tables(conn=None):
    close_at_end = False
    if conn is None:
        conn = get_conn()
        close_at_end = True
    c = conn.cursor()

    tables = [
        """
        CREATE TABLE IF NOT EXISTS grievances (
            id TEXT PRIMARY KEY,
            ticket_id TEXT UNIQUE NOT NULL,
            user_id TEXT,
            citizen_name TEXT,
            contact TEXT,
            area TEXT,
            location TEXT,
            original_text TEXT NOT NULL,
            summary TEXT,
            language TEXT DEFAULT 'en',
            translated_text TEXT,
            department TEXT,
            category TEXT,
            confidence REAL,
            routing_reason TEXT,
            priority TEXT DEFAULT 'Medium',
            priority_reason TEXT,
            status TEXT DEFAULT 'Submitted',
            sla_due_at TEXT,
            escalation_level INTEGER DEFAULT 0,
            cluster_id TEXT,
            needs_review INTEGER DEFAULT 0,
            pin_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS clusters (
            cluster_id TEXT PRIMARY KEY,
            department TEXT,
            category TEXT,
            area TEXT,
            report_count INTEGER DEFAULT 1,
            first_reported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_reported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            representative_ticket_id TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS grievance_history (
            id TEXT PRIMARY KEY,
            ticket_id TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            actor TEXT DEFAULT 'Citizen',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS grievance_feedback (
            id TEXT PRIMARY KEY,
            ticket_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]

    for ddl in tables:
        c.execute(ddl)

    try:
        c.execute("PRAGMA table_info(grievances)")
        cols = {row[1].lower() for row in c.fetchall()}
        if cols and "pin_hash" not in cols:
            c.execute("ALTER TABLE grievances ADD COLUMN pin_hash TEXT")
    except Exception:
        pass

    conn.commit()
    if close_at_end:
        conn.close()

def _generate_ticket_id(c) -> str:
    _exec(c, "SELECT ticket_id FROM grievances WHERE ticket_id LIKE 'GRV-%'")
    rows = c.fetchall()
    max_num = 1000
    for r in rows:
        val = r[0] if not isinstance(r, dict) else r["ticket_id"]
        try:
            num = int(val.replace("GRV-", ""))
            if num > max_num:
                max_num = num
        except Exception:
            pass
    return f"GRV-{max_num + 1}"

def create_grievance(data: dict) -> str:
    conn = get_conn()
    c = conn.cursor()

    gid = str(uuid.uuid4())
    ticket_id = _generate_ticket_id(c)

    priority = data.get("priority", "Medium")
    if priority not in SLA_HOURS:
        priority = priority.capitalize()
        if priority not in SLA_HOURS:
            priority = "Medium"

    now_dt = datetime.utcnow()
    sla_hours = SLA_HOURS.get(priority, 168)
    sla_due_at = (now_dt + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M:%S")
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    status = data.get("status", "Submitted")

    pin_hash = None
    if data.get("pin"):
        pin_hash = bcrypt.hashpw(str(data["pin"]).encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    elif data.get("pin_hash"):
        pin_hash = data["pin_hash"]

    sql = f"""
    INSERT INTO grievances (
        id, ticket_id, user_id, citizen_name, contact, area, location,
        original_text, summary, language, translated_text, department, category,
        confidence, routing_reason, priority, priority_reason, status,
        sla_due_at, escalation_level, cluster_id, needs_review, pin_hash, created_at, updated_at
    ) VALUES (
        {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()},
        {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()},
        {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()},
        {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}
    )
    """

    params = (
        gid,
        ticket_id,
        data.get("user_id"),
        data.get("citizen_name"),
        data.get("contact"),
        data.get("area"),
        data.get("location"),
        data.get("original_text", ""),
        data.get("summary"),
        data.get("language", "en"),
        data.get("translated_text"),
        data.get("department"),
        data.get("category"),
        data.get("confidence"),
        data.get("routing_reason"),
        priority,
        data.get("priority_reason"),
        status,
        sla_due_at,
        data.get("escalation_level", 0),
        data.get("cluster_id"),
        data.get("needs_review", 0),
        pin_hash,
        now_str,
        now_str
    )

    _exec(c, sql, params)

    hist_id = str(uuid.uuid4())
    hist_sql = f"""
    INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at)
    VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})
    """
    _exec(c, hist_sql, (hist_id, ticket_id, status, "Grievance submitted", data.get("citizen_name") or "Citizen", now_str))

    conn.commit()
    conn.close()
    return ticket_id

def create_cluster(department: str, category: str, area: str, representative_ticket_id: str = None) -> str:
    conn = get_conn()
    c = conn.cursor()
    cluster_id = f"CLU-{str(uuid.uuid4())[:8].upper()}"
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    sql = f"""
    INSERT INTO clusters (
        cluster_id, department, category, area, report_count,
        first_reported_at, last_reported_at, representative_ticket_id
    ) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, 1, {_ph()}, {_ph()}, {_ph()})
    """
    _exec(c, sql, (cluster_id, department, category, area, now_str, now_str, representative_ticket_id))

    if representative_ticket_id:
        _exec(c, f"UPDATE grievances SET cluster_id = {_ph()} WHERE ticket_id = {_ph()}",
              (cluster_id, representative_ticket_id))

    conn.commit()
    conn.close()
    return cluster_id

def attach_to_cluster(ticket_id: str, cluster_id: str) -> bool:
    conn = get_conn()
    c = conn.cursor()
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    _exec(c, f"UPDATE grievances SET cluster_id = {_ph()}, updated_at = {_ph()} WHERE ticket_id = {_ph()}",
          (cluster_id, now_str, ticket_id))
    if c.rowcount == 0:
        conn.close()
        return False

    _exec(c, f"UPDATE clusters SET report_count = report_count + 1, last_reported_at = {_ph()} WHERE cluster_id = {_ph()}",
          (now_str, cluster_id))

    conn.commit()
    conn.close()
    return True

def list_clusters() -> list:
    conn = get_conn()
    c = conn.cursor()
    _exec(c, "SELECT * FROM clusters ORDER BY report_count DESC")
    rows = [_row_to_dict(r, c) for r in c.fetchall()]
    conn.close()
    return rows

def _enrich_overdue(grievance: dict, now_dt: Optional[datetime] = None):
    """Enrich grievance dict with overdue (bool) and hours_overdue (float)."""
    if now_dt is None:
        now_dt = datetime.utcnow()
    sla_str = grievance.get("sla_due_at")
    is_resolved = (grievance.get("status") == "Resolved")
    if sla_str and not is_resolved:
        try:
            sla_dt = datetime.strptime(str(sla_str)[:19], "%Y-%m-%d %H:%M:%S")
            diff = (now_dt - sla_dt).total_seconds() / 3600.0
            grievance["overdue"] = diff > 0
            grievance["hours_overdue"] = round(diff, 1) if diff > 0 else 0.0
        except Exception:
            grievance["overdue"] = False
            grievance["hours_overdue"] = 0.0
    else:
        grievance["overdue"] = False
        grievance["hours_overdue"] = 0.0

def get_grievance(ticket_id: str, now: Optional[datetime] = None) -> dict:
    conn = get_conn()
    c = conn.cursor()

    _exec(c, f"SELECT * FROM grievances WHERE ticket_id = {_ph()}", (ticket_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None

    grievance = _row_to_dict(row, c)

    _exec(c, f"SELECT * FROM grievance_history WHERE ticket_id = {_ph()} ORDER BY created_at ASC", (ticket_id,))
    grievance["history"] = [_row_to_dict(r, c) for r in c.fetchall()]

    _exec(c, f"SELECT * FROM grievance_feedback WHERE ticket_id = {_ph()} ORDER BY created_at ASC", (ticket_id,))
    grievance["feedback"] = [_row_to_dict(r, c) for r in c.fetchall()]

    # If associated with a cluster, enrich cluster report count
    if grievance.get("cluster_id"):
        _exec(c, f"SELECT report_count FROM clusters WHERE cluster_id = {_ph()}", (grievance["cluster_id"],))
        crow = c.fetchone()
        if crow:
            grievance["report_count"] = crow[0] if not isinstance(crow, dict) else crow["report_count"]
            grievance["cluster_report_count"] = grievance["report_count"]

    conn.close()
    _enrich_overdue(grievance, now)
    return grievance

def list_grievances(
    status=None,
    department=None,
    priority=None,
    language=None,
    area=None,
    overdue: Optional[bool] = None,
    needs_review: Optional[bool] = None,
    limit=100
) -> list:
    conn = get_conn()
    c = conn.cursor()

    now_dt = datetime.utcnow()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    clauses = []
    params = []

    if status:
        clauses.append(f"status = {_ph()}")
        params.append(status)
    if department:
        clauses.append(f"department = {_ph()}")
        params.append(department)
    if priority:
        clauses.append(f"priority = {_ph()}")
        params.append(priority)
    if language:
        clauses.append(f"language = {_ph()}")
        params.append(language)
    if area:
        clauses.append(f"(area = {_ph()} OR location = {_ph()})")
        params.extend([area, area])
    if needs_review is True:
        clauses.append("needs_review = 1")
    elif needs_review is False:
        clauses.append("(needs_review = 0 OR needs_review IS NULL)")

    if overdue is True:
        clauses.append(f"status != 'Resolved' AND sla_due_at IS NOT NULL AND sla_due_at < {_ph()}")
        params.append(now_str)
    elif overdue is False:
        clauses.append(f"(status = 'Resolved' OR sla_due_at IS NULL OR sla_due_at >= {_ph()})")
        params.append(now_str)

    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM grievances {where_sql} ORDER BY created_at DESC LIMIT {int(limit)}"
    _exec(c, sql, tuple(params))

    rows = [_row_to_dict(r, c) for r in c.fetchall()]
    conn.close()

    for r in rows:
        _enrich_overdue(r, now_dt)
        r.pop("pin_hash", None)
        r["needs_review"] = int(r.get("needs_review") or 0)
        r["escalation_level"] = int(r.get("escalation_level") or 0)
        if not r.get("location") and r.get("area"):
            r["location"] = r["area"]
        if not r.get("area") and r.get("location"):
            r["area"] = r["location"]

    return rows

def update_status(ticket_id: str, status: str, note: str = "", actor: str = "System") -> bool:
    conn = get_conn()
    c = conn.cursor()

    now_dt = datetime.utcnow()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    _exec(c, f"SELECT priority FROM grievances WHERE ticket_id = {_ph()}", (ticket_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False

    priority = (row[0] if not isinstance(row, dict) else row["priority"]) or "Medium"
    sla_hours = SLA_HOURS.get(priority, 168)

    if status.lower() == "reopened":
        fresh_due_at = (now_dt + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M:%S")
        _exec(c, f"UPDATE grievances SET status = {_ph()}, updated_at = {_ph()}, sla_due_at = {_ph()}, escalation_level = 0 WHERE ticket_id = {_ph()}",
              (status, now_str, fresh_due_at, ticket_id))
    else:
        _exec(c, f"UPDATE grievances SET status = {_ph()}, updated_at = {_ph()} WHERE ticket_id = {_ph()}",
              (status, now_str, ticket_id))

    if c.rowcount == 0:
        conn.close()
        return False

    hist_id = str(uuid.uuid4())
    _exec(c, f"INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
          (hist_id, ticket_id, status, note, actor, now_str))

    conn.commit()
    conn.close()
    return True

def reset_pin(ticket_id: str, new_pin: str, actor: str = "Admin") -> bool:
    conn = get_conn()
    c = conn.cursor()
    pin_hash = bcrypt.hashpw(str(new_pin).encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    _exec(c, f"SELECT status FROM grievances WHERE ticket_id = {_ph()}", (ticket_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    curr_status = row[0] if not isinstance(row, dict) else row["status"]

    _exec(c, f"UPDATE grievances SET pin_hash = {_ph()}, updated_at = {_ph()} WHERE ticket_id = {_ph()}",
          (pin_hash, now_str, ticket_id))
    if c.rowcount == 0:
        conn.close()
        return False

    hist_id = str(uuid.uuid4())
    _exec(c, f"INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
          (hist_id, ticket_id, curr_status, "PIN reset", actor, now_str))

    conn.commit()
    conn.close()
    return True

def run_escalation(now: Optional[datetime] = None) -> int:
    """
    Idempotent SLA escalation check.
    Sets escalation_level:
      1 once overdue (past sla_due_at)
      2 when overdue by > 50% of SLA window
      3 when overdue by > 100% of SLA window
    Only writes a history row when escalation_level increases.
    """
    conn = get_conn()
    c = conn.cursor()

    now_dt = now if now is not None else datetime.utcnow()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    _exec(c, f"SELECT ticket_id, status, priority, sla_due_at, escalation_level FROM grievances WHERE status != {_ph()} AND sla_due_at IS NOT NULL", ("Resolved",))
    rows = [_row_to_dict(r, c) for r in c.fetchall()]

    escalated_count = 0
    for row in rows:
        sla_str = row.get("sla_due_at")
        if not sla_str:
            continue
        try:
            sla_dt = datetime.strptime(str(sla_str)[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue

        priority = row.get("priority", "Medium")
        sla_window = float(SLA_HOURS.get(priority, 168))
        diff_hours = (now_dt - sla_dt).total_seconds() / 3600.0

        if diff_hours <= 0:
            target_level = 0
        elif diff_hours > 1.0 * sla_window:
            target_level = 3
        elif diff_hours > 0.5 * sla_window:
            target_level = 2
        else:
            target_level = 1

        curr_level = int(row.get("escalation_level") or 0)
        if target_level > curr_level:
            tid = row["ticket_id"]
            curr_status = row.get("status", "Submitted")
            _exec(c, f"UPDATE grievances SET escalation_level = {_ph()}, updated_at = {_ph()} WHERE ticket_id = {_ph()}",
                  (target_level, now_str, tid))
            hist_id = str(uuid.uuid4())
            _exec(c, f"INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
                  (hist_id, tid, curr_status, f"SLA breached, escalated to level {target_level}", "System", now_str))
            escalated_count += 1

    conn.commit()
    conn.close()
    return escalated_count

def add_feedback(ticket_id: str, rating: int, comment: str = "") -> dict:
    conn = get_conn()
    c = conn.cursor()

    fb_id = str(uuid.uuid4())
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    _exec(c, f"INSERT INTO grievance_feedback (id, ticket_id, rating, comment, created_at) VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
          (fb_id, ticket_id, rating, comment, now_str))

    _exec(c, f"SELECT status FROM grievances WHERE ticket_id = {_ph()}", (ticket_id,))
    row = c.fetchone()
    if row:
        curr_status = row[0] if not isinstance(row, dict) else row["status"]
        if rating in (1, 2) and curr_status.lower() == "resolved":
            conn.close()
            update_status(ticket_id, "Reopened", note="Reopened due to citizen feedback", actor="Citizen")
            return {"id": fb_id, "ticket_id": ticket_id, "rating": rating, "comment": comment}

    conn.commit()
    conn.close()
    return {"id": fb_id, "ticket_id": ticket_id, "rating": rating, "comment": comment}

def find_open_in_area(area: str, department: str) -> list:
    conn = get_conn()
    c = conn.cursor()

    _exec(c, f"SELECT * FROM grievances WHERE area = {_ph()} AND department = {_ph()} AND status != {_ph()} ORDER BY created_at DESC",
          (area, department, "Resolved"))
    rows = [_row_to_dict(r, c) for r in c.fetchall()]
    conn.close()
    return rows

def get_stats() -> dict:
    conn = get_conn()
    c = conn.cursor()
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Status
    _exec(c, "SELECT status, COUNT(*) as cnt FROM grievances GROUP BY status")
    by_status = {r[0] if not isinstance(r, dict) else r["status"]: r[1] if not isinstance(r, dict) else r["cnt"] for r in c.fetchall()}

    # Department
    _exec(c, "SELECT department, COUNT(*) as cnt FROM grievances WHERE department IS NOT NULL GROUP BY department")
    by_department = {r[0] if not isinstance(r, dict) else r["department"]: r[1] if not isinstance(r, dict) else r["cnt"] for r in c.fetchall()}

    # Priority
    _exec(c, "SELECT priority, COUNT(*) as cnt FROM grievances GROUP BY priority")
    by_priority = {r[0] if not isinstance(r, dict) else r["priority"]: r[1] if not isinstance(r, dict) else r["cnt"] for r in c.fetchall()}

    # Language
    _exec(c, "SELECT language, COUNT(*) as cnt FROM grievances WHERE language IS NOT NULL GROUP BY language")
    by_language = {r[0] if not isinstance(r, dict) else r["language"]: r[1] if not isinstance(r, dict) else r["cnt"] for r in c.fetchall()}

    # Hotspots (top areas by complaint count)
    _exec(c, "SELECT area, COUNT(*) as cnt FROM grievances WHERE area IS NOT NULL AND area != '' GROUP BY area ORDER BY cnt DESC LIMIT 10")
    hotspots = {r[0] if not isinstance(r, dict) else r["area"]: r[1] if not isinstance(r, dict) else r["cnt"] for r in c.fetchall()}

    # Clusters summary
    _exec(c, "SELECT cluster_id, report_count FROM clusters ORDER BY report_count DESC")
    clusters_data = {r[0] if not isinstance(r, dict) else r["cluster_id"]: r[1] if not isinstance(r, dict) else r["report_count"] for r in c.fetchall()}

    # Daily last 14 days
    today = datetime.utcnow().date()
    daily_counts = {}
    for i in range(13, -1, -1):
        day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_counts[day_str] = 0

    _exec(c, "SELECT created_at FROM grievances")
    for r in c.fetchall():
        dt_val = r[0] if not isinstance(r, dict) else r["created_at"]
        if dt_val:
            day_str = str(dt_val)[:10]
            if day_str in daily_counts:
                daily_counts[day_str] += 1

    # Resolution hours overall and per department
    _exec(c, f"SELECT department, created_at, updated_at FROM grievances WHERE status = {_ph()}", ("Resolved",))
    resolved_rows = c.fetchall()
    total_hours = 0.0
    count_resolved = 0
    dept_times = {}

    for r in resolved_rows:
        dept = r[0] if not isinstance(r, dict) else r["department"]
        dept = dept or "Unassigned"
        c_at = r[1] if not isinstance(r, dict) else r["created_at"]
        u_at = r[2] if not isinstance(r, dict) else r["updated_at"]
        if c_at and u_at:
            try:
                t1 = datetime.strptime(str(c_at)[:19], "%Y-%m-%d %H:%M:%S")
                t2 = datetime.strptime(str(u_at)[:19], "%Y-%m-%d %H:%M:%S")
                diff = (t2 - t1).total_seconds() / 3600.0
                if diff >= 0:
                    total_hours += diff
                    count_resolved += 1
                    dept_times.setdefault(dept, []).append(diff)
            except Exception:
                pass

    avg_resolution_hours = round(total_hours / count_resolved, 2) if count_resolved > 0 else 0.0
    avg_resolution_by_dept = {d: round(sum(times) / len(times), 2) for d, times in dept_times.items()}

    # Overdue counts overall and per department
    _exec(c, f"SELECT department, COUNT(*) as cnt FROM grievances WHERE status != 'Resolved' AND sla_due_at IS NOT NULL AND sla_due_at < {_ph()} GROUP BY department", (now_str,))
    overdue_by_dept = {r[0] if not isinstance(r, dict) else r["department"]: r[1] if not isinstance(r, dict) else r["cnt"] for r in c.fetchall()}
    overdue_count = sum(overdue_by_dept.values())

    # Escalation level breakdown
    _exec(c, "SELECT escalation_level, COUNT(*) as cnt FROM grievances GROUP BY escalation_level")
    by_escalation_level = {int(r[0] if not isinstance(r, dict) else r["escalation_level"] or 0): r[1] if not isinstance(r, dict) else r["cnt"] for r in c.fetchall()}
    for lvl in (0, 1, 2, 3):
        by_escalation_level.setdefault(lvl, 0)

    conn.close()
    return {
        "by_status": by_status,
        "by_department": by_department,
        "by_priority": by_priority,
        "by_language": by_language,
        "hotspots": hotspots,
        "clusters": {
            "total_clusters": len(clusters_data),
            "cluster_counts": clusters_data
        },
        "daily_counts": daily_counts,
        "avg_resolution_hours": avg_resolution_hours,
        "avg_resolution_by_dept": avg_resolution_by_dept,
        "overdue_count": overdue_count,
        "overdue_by_dept": overdue_by_dept,
        "by_escalation_level": by_escalation_level
    }

def reroute_grievance(ticket_id: str, department: str, category: str, note: str, actor: str) -> bool:
    conn = get_conn()
    c = conn.cursor()
    now_dt = datetime.utcnow()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    _exec(c, f"SELECT status, department FROM grievances WHERE ticket_id = {_ph()}", (ticket_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False

    curr_status = row[0] if not isinstance(row, dict) else row["status"]
    old_dept = row[1] if not isinstance(row, dict) else row["department"]

    _exec(c, f"""
        UPDATE grievances
        SET department = {_ph()},
            category = {_ph()},
            needs_review = 0,
            routing_reason = 'Manually routed by admin',
            updated_at = {_ph()}
        WHERE ticket_id = {_ph()}
    """, (department, category, now_str, ticket_id))

    if c.rowcount == 0:
        conn.close()
        return False

    hist_id = str(uuid.uuid4())
    hist_note = f"Re-routed from {old_dept} to {department}: {note}"
    _exec(c, f"""
        INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at)
        VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})
    """, (hist_id, ticket_id, curr_status, hist_note, actor, now_str))

    conn.commit()
    conn.close()
    return True

def flag_misrouted(ticket_id: str, note: str, actor: str) -> bool:
    conn = get_conn()
    c = conn.cursor()
    now_dt = datetime.utcnow()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    _exec(c, f"SELECT status FROM grievances WHERE ticket_id = {_ph()}", (ticket_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False

    curr_status = row[0] if not isinstance(row, dict) else row["status"]

    _exec(c, f"""
        UPDATE grievances
        SET needs_review = 1,
            updated_at = {_ph()}
        WHERE ticket_id = {_ph()}
    """, (now_str, ticket_id))

    if c.rowcount == 0:
        conn.close()
        return False

    hist_id = str(uuid.uuid4())
    hist_note = f"Flagged as misrouted: {note}"
    _exec(c, f"""
        INSERT INTO grievance_history (id, ticket_id, status, note, actor, created_at)
        VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})
    """, (hist_id, ticket_id, curr_status, hist_note, actor, now_str))

    conn.commit()
    conn.close()
    return True

def get_audit_log(limit: int = 100, offset: int = 0) -> list:
    conn = get_conn()
    c = conn.cursor()
    sql = f"""
    SELECT h.ticket_id, g.department, h.status, h.note, h.actor, h.created_at
    FROM grievance_history h
    LEFT JOIN grievances g ON h.ticket_id = g.ticket_id
    ORDER BY h.created_at DESC
    LIMIT {_ph()} OFFSET {_ph()}
    """
    _exec(c, sql, (int(limit), int(offset)))
    rows = [_row_to_dict(r, c) for r in c.fetchall()]
    conn.close()
    return rows
