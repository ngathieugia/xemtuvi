"""File khởi động cho cPanel "Setup Python App" khi tạo app RIÊNG cho bot PI.

Application startup file: pi_alert_wsgi.py
Application Entry point:  application
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pi_alert.web import create_app  # noqa: E402

application = create_app()
