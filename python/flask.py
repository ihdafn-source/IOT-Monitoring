@app.route("/alert", methods=["POST"])
def alert():
    data = request.json
    print("Alert masuk:", data)

    settings = load_settings()
    if not settings.get("notif_enabled", True):
        print("Notifikasi nonaktif, alert tidak dikirim")
        return {"status": "skipped", "reason": "notif dinonaktifkan"}

    alerts = data.get("alerts", [])

    for a in alerts:
        status = a.get("status")  # "firing" atau "resolved"
        labels = a.get("labels", {})
        values = a.get("values", {})  # nilai numerik dari query, misal {"B": 18.2}

        nilai = list(values.values())[0] if values else "tidak diketahui"

        message = f"""
🚨 ALERT POMPA ({status.upper()})

Sensor: {labels.get('alertname', 'Ultrasonic')}

Jarak terdeteksi:
{nilai} cm

Threshold testing: 20 cm

Cek dashboard Grafana.
"""
        send_telegram(message)

    return {"status": "ok"}