"""
ParticleHub configuration file template.
Default log database is InfluxDB
"""
cloud_api_token = ""
csrf_key = ""
default_log_source = "influx"
influx_db_name = ""
influx_user = ""
influx_password = ""
influx_host = ""
influx_port = 8086
syslog_host = ("", 5000)
web_host = "0.0.0.0"
log_config = {"influx": dict(host=influx_host,
                             port=influx_port,
                             username=influx_user,
                             password=influx_password,
                             database=influx_db_name)}
stream_config = {"url": "https://api.particle.io/v1/devices/events?access_token=%s" % cloud_api_token}
