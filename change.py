@app.route("/server_dashboard")
def server_dashboard():
    """This function displays the HTML page for the dashboard."""
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.*
        FROM agents a
        INNER JOIN (
            SELECT hostname, MAX(last_heartbeat) AS max_hb
            FROM agents
            GROUP BY hostname
        ) b
        ON a.hostname = b.hostname AND a.last_heartbeat = b.max_hb
        ORDER BY a.last_heartbeat DESC;
    """)
    agents = cur.fetchall()
    conn.close()

    unique_ips = len({agent["ip_address"] for agent in agents})
    latest_heartbeat = agents[0]["last_heartbeat"] if agents else None

    now_utc = datetime.now(timezone.utc)
    for agent in agents:
        last_hb_aware = agent["last_heartbeat"].replace(tzinfo=timezone.utc)
        diff = (now_utc - last_hb_aware).total_seconds()
        agent["status"] = "Active" if diff <= ACTIVE_THRESHOLD_SECONDS else "Inactive"

    return render_template(
        "server_dashboard.html",
        logs=agents,
        unique_ips=unique_ips,
        latest_download_time=latest_heartbeat.strftime('%Y-%m-%d %H:%M:%S') if latest_heartbeat else "N/A"
    )
