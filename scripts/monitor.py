"""
Anti-Filter Bridge Monitor

This script monitors the Anti-Filter Bridge service and provides alerts,
performance metrics, and health checks.
"""
import argparse
import asyncio
import json
import logging
import os
import platform
import psutil
import signal
import socket
import ssl
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('monitor.log')
    ]
)
logger = logging.getLogger('AFBMonitor')

# Default configuration
DEFAULT_CONFIG = {
    'monitor': {
        'check_interval': '60',  # seconds
        'alert_interval': '300',  # seconds
        'log_retention_days': '7',
        'metrics_enabled': 'true',
        'alerts_enabled': 'true',
    },
    'server': {
        'host': '127.0.0.1',
        'port': '8443',
        'use_ssl': 'true',
        'verify_ssl': 'false',
        'auth_token': '',
    },
    'alerts': {
        'cpu_threshold': '80',  # percentage
        'memory_threshold': '80',  # percentage
        'disk_threshold': '85',  # percentage
        'max_log_size': '10485760',  # 10MB
        'email_notifications': 'false',
        'email_server': '',
        'email_port': '587',
        'email_username': '',
        'email_password': '',
        'email_from': '',
        'email_to': '',
    },
    'web_interface': {
        'enabled': 'true',
        'host': '127.0.0.1',
        'port': '8080',
        'username': 'admin',
        'password': 'admin123',  # Change this in production!
    },
}

class AFBMonitor:
    """A class to monitor the Anti-Filter Bridge service."""
    
    def __init__(self, config_file: str = None):
        """Initialize the monitor.
        
        Args:
            config_file: Path to a configuration file
        """
        self.config = self._load_config(config_file)
        self.running = False
        self.metrics = {
            'start_time': time.time(),
            'checks': 0,
            'alerts_triggered': 0,
            'last_check': None,
            'last_alert': {},
            'service_status': 'unknown',
            'performance_metrics': {},
        }
        self.alert_history = []
        self._setup_signal_handlers()
    
    def _load_config(self, config_file: str = None) -> configparser.ConfigParser:
        """Load configuration from file or use defaults.
        
        Args:
            config_file: Path to a configuration file
            
        Returns:
            A ConfigParser object with the loaded configuration
        """
        config = configparser.ConfigParser()
        
        # Set default values
        for section, options in DEFAULT_CONFIG.items():
            config[section] = options
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            try:
                config.read(config_file)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
               
        return config
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, self._handle_shutdown)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutdown signal received. Stopping monitor...")
        self.running = False
    
    async def check_service_status(self) -> Dict[str, any]:
        """Check the status of the Anti-Filter Bridge service.
        
        Returns:
            A dictionary containing service status information
        """
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'unknown',
            'process': None,
            'ports': [],
            'errors': []
        }
        
        # Check if the process is running
        process_name = 'python' if platform.system() == 'Windows' else 'python3'
        process_found = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Look for the Anti-Filter Bridge process
                if (proc.info['name'] == process_name and 
                    'anti_filter_bridge' in ' '.join(proc.info['cmdline'] or [])):
                    status['process'] = {
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': ' '.join(proc.info['cmdline'] or []),
                        'create_time': proc.create_time(),
                        'status': proc.status(),
                        'cpu_percent': proc.cpu_percent(interval=0.1),
                        'memory_percent': proc.memory_percent(),
                        'num_threads': proc.num_threads(),
                        'connections': [
                            {
                                'fd': conn.fd,
                                'family': conn.family.name,
                                'type': conn.type.name,
                                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if hasattr(conn.laddr, 'ip') else str(conn.laddr),
                                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if hasattr(conn, 'raddr') and conn.raddr else None,
                                'status': conn.status
                            }
                            for conn in proc.connections()
                        ]
                    }
                    process_found = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                status['errors'].append(f"Error checking process {proc.pid if 'pid' in proc.info else 'unknown'}: {e}")
        
        if not process_found:
            status['errors'].append("Anti-Filter Bridge process not found")
        
        # Check if the service is listening on the expected ports
        expected_ports = [
            int(self.config['server'].get('port', 8443)),
            int(self.config['web_interface'].get('port', 8080)) if self.config['web_interface'].getboolean('enabled', True) else None
        ]
        
        for port in expected_ports:
            if not port:
                continue
                
            is_listening = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    is_listening = s.connect_ex(('127.0.0.1', port)) == 0
            except Exception as e:
                status['errors'].append(f"Error checking port {port}: {e}")
            
            status['ports'].append({
                'port': port,
                'listening': is_listening
            })
        
        # Determine overall status
        if process_found and all(port['listening'] for port in status['ports']):
            status['service'] = 'running'
        elif process_found:
            status['service'] = 'degraded'
        else:
            status['service'] = 'stopped'
        
        # Update metrics
        self.metrics['service_status'] = status['service']
        self.metrics['last_check'] = datetime.utcnow().isoformat()
        self.metrics['checks'] += 1
        
        return status
    
    async def check_system_metrics(self) -> Dict[str, any]:
        """Collect system performance metrics.
        
        Returns:
            A dictionary containing system metrics
        """
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'percent': psutil.virtual_memory().percent,
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent,
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv,
                'packets_sent': psutil.net_io_counters().packets_sent,
                'packets_recv': psutil.net_io_counters().packets_recv,
                'err_in': psutil.net_io_counters().errin,
                'err_out': psutil.net_io_counters().errout,
                'drop_in': psutil.net_io_counters().dropin,
                'drop_out': psutil.net_io_counters().dropout,
            },
            'processes': {
                'total': len(psutil.pids()),
                'running': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running']),
                'sleeping': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'sleeping']),
                'idle': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'idle']),
                'zombie': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'zombie']),
            },
        }
        
        # Update metrics
        self.metrics['performance_metrics'] = metrics
        
        return metrics
    
    async def check_alerts(self, status: Dict[str, any], metrics: Dict[str, any]) -> List[Dict[str, any]]:
        """Check for alert conditions.
        
        Args:
            status: Service status from check_service_status()
            metrics: System metrics from check_system_metrics()
            
        Returns:
            A list of triggered alerts
        """
        alerts = []
        now = datetime.utcnow()
        
        # Service status alerts
        if status['service'] == 'stopped':
            alerts.append({
                'level': 'critical',
                'message': 'Anti-Filter Bridge service is not running',
                'timestamp': now.isoformat(),
                'type': 'service_status',
                'data': status
            })
        elif status['service'] == 'degraded':
            failed_ports = [port['port'] for port in status['ports'] if not port['listening']]
            alerts.append({
                'level': 'warning',
                'message': f"Service is running but not listening on expected ports: {', '.join(map(str, failed_ports))}",
                'timestamp': now.isoformat(),
                'type': 'service_degraded',
                'data': {
                    'failed_ports': failed_ports,
                    'status': status
                }
            })
        
        # CPU usage alert
        cpu_threshold = float(self.config['alerts'].get('cpu_threshold', 80))
        if metrics['cpu']['percent'] > cpu_threshold:
            alerts.append({
                'level': 'warning',
                'message': f'High CPU usage: {metrics["cpu"]["percent"]:.1f}%',
                'timestamp': now.isoformat(),
                'type': 'high_cpu',
                'data': metrics['cpu']
            })
        
        # Memory usage alert
        memory_threshold = float(self.config['alerts'].get('memory_threshold', 80))
        if metrics['memory']['percent'] > memory_threshold:
            alerts.append({
                'level': 'warning',
                'message': f'High memory usage: {metrics["memory"]["percent"]:.1f}%',
                'timestamp': now.isoformat(),
                'type': 'high_memory',
                'data': metrics['memory']
            })
        
        # Disk usage alert
        disk_threshold = float(self.config['alerts'].get('disk_threshold', 85))
        if metrics['disk']['percent'] > disk_threshold:
            alerts.append({
                'level': 'warning',
                'message': f'High disk usage: {metrics["disk"]["percent"]:.1f}%',
                'timestamp': now.isoformat(),
                'type': 'high_disk',
                'data': metrics['disk']
            })
        
        # Process alert
        if status.get('process'):
            process = status['process']
            
            # High process CPU
            if process.get('cpu_percent', 0) > 90:
                alerts.append({
                    'level': 'warning',
                    'message': f'High process CPU usage: {process["cpu_percent"]:.1f}%',
                    'timestamp': now.isoformat(),
                    'type': 'high_process_cpu',
                    'data': process
                })
            
            # High process memory
            if process.get('memory_percent', 0) > 50:
                alerts.append({
                    'level': 'warning',
                    'message': f'High process memory usage: {process["memory_percent"]:.1f}%',
                    'timestamp': now.isoformat(),
                    'type': 'high_process_memory',
                    'data': process
                })
        
        # Check for repeated errors in logs
        log_file = self.config['monitor'].get('log_file', 'antifilterbridge.log')
        if os.path.exists(log_file):
            try:
                # Count error lines in the last hour
                one_hour_ago = now - timedelta(hours=1)
                error_count = 0
                
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if 'ERROR' in line or 'CRITICAL' in line:
                            # Extract timestamp from log line (assuming a standard format)
                            try:
                                log_time_str = ' '.join(line.split()[:2])
                                log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S,%f')
                                if log_time > one_hour_ago:
                                    error_count += 1
                            except (ValueError, IndexError):
                                continue
                
                if error_count > 10:  # More than 10 errors in the last hour
                    alerts.append({
                        'level': 'warning',
                        'message': f'High error rate in logs: {error_count} errors in the last hour',
                        'timestamp': now.isoformat(),
                        'type': 'high_error_rate',
                        'data': {
                            'error_count': error_count,
                            'time_window': '1h'
                        }
                    })
                    
            except Exception as e:
                logger.error(f"Error checking log file: {e}")
        
        # Check if we should suppress this alert due to recent firing
        suppressed_alerts = []
        alert_interval = int(self.config['monitor'].get('alert_interval', 300))
        
        for alert in alerts:
            alert_key = f"{alert['type']}_{alert.get('message', '')[:50]}"
            last_alert_time = self.metrics['last_alert'].get(alert_key)
            
            if last_alert_time and (now - last_alert_time).total_seconds() < alert_interval:
                # Suppress this alert as it was recently triggered
                continue
            
            # This is a new alert or the cooldown has passed
            self.metrics['last_alert'][alert_key] = now
            suppressed_alerts.append(alert)
        
        # Update metrics
        self.metrics['alerts_triggered'] += len(suppressed_alerts)
        
        # Log and handle alerts
        for alert in suppressed_alerts:
            logger.warning(f"ALERT [{alert['level'].upper()}] {alert['message']}")
            self.alert_history.append(alert)
            
            # Keep only the last 100 alerts in history
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]
            
            # Send email notification if enabled
            if (self.config['alerts'].getboolean('email_notifications', False) and 
                alert['level'] in ['critical', 'warning']):
                self._send_email_alert(alert)
        
        return suppressed_alerts
    
    def _send_email_alert(self, alert: Dict[str, any]):
        """Send an email alert.
        
        Args:
            alert: Alert details
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Skip if email settings are not configured
            if not all([
                self.config['alerts'].get('email_server'),
                self.config['alerts'].get('email_username'),
                self.config['alerts'].get('email_password'),
                self.config['alerts'].get('email_from'),
                self.config['alerts'].get('email_to')
            ]):
                logger.warning("Email alerting enabled but email settings are incomplete")
                return
            
            # Create message
            subject = f"[{alert['level'].upper()}] Anti-Filter Bridge Alert: {alert['message'][:50]}..."
            
            msg = MIMEMultipart()
            msg['From'] = self.config['alerts']['email_from']
            msg['To'] = self.config['alerts']['email_to']
            msg['Subject'] = subject
            
            # Create email body
            body = f"""
            <h2>Anti-Filter Bridge Alert</h2>
            <p><strong>Level:</strong> {alert['level'].upper()}</p>
            <p><strong>Time:</strong> {alert['timestamp']}</p>
            <p><strong>Message:</strong> {alert['message']}</p>
            """
            
            # Add alert data as JSON
            import json
            body += "<h3>Alert Details:</h3>"
            body += f"<pre>{json.dumps(alert.get('data', {}), indent=2)}</pre>"
            
            # Add system metrics if available
            if hasattr(self, 'metrics') and 'performance_metrics' in self.metrics:
                body += "<h3>System Metrics:</h3>"
                body += f"<pre>{json.dumps(self.metrics['performance_metrics'], indent=2)}</pre>"
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(
                self.config['alerts']['email_server'],
                int(self.config['alerts'].get('email_port', 587))
            ) as server:
                if self.config['alerts'].get('email_port') == '587':
                    server.starttls()
                
                server.login(
                    self.config['alerts']['email_username'],
                    self.config['alerts']['email_password']
                )
                
                server.send_message(msg)
                logger.info(f"Email alert sent to {self.config['alerts']['email_to']}")
                
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def start_web_interface(self):
        """Start the web interface for monitoring."""
        if not self.config['web_interface'].getboolean('enabled', True):
            logger.info("Web interface is disabled in configuration")
            return
        
        try:
            from fastapi import FastAPI, Request, Depends, HTTPException, status
            from fastapi.security import HTTPBasic, HTTPBasicCredentials
            from fastapi.staticfiles import StaticFiles
            from fastapi.templating import Jinja2Templates
            from fastapi.responses import HTMLResponse, JSONResponse
            from fastapi.middleware.cors import CORSMiddleware
            
            app = FastAPI(title="Anti-Filter Bridge Monitor")
            
            # Enable CORS if needed
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # Set up templates
            templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
            os.makedirs(templates_dir, exist_ok=True)
            
            # Create a default template if it doesn't exist
            index_template = os.path.join(templates_dir, 'index.html')
            if not os.path.exists(index_template):
                with open(index_template, 'w') as f:
                    f.write("""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Anti-Filter Bridge Monitor</title>
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                        <style>
                            .card { margin-bottom: 20px; }
                            .status-card { text-align: center; padding: 20px; }
                            .status-running { background-color: #d4edda; }
                            .status-stopped { background-color: #f8d7da; }
                            .status-degraded { background-color: #fff3cd; }
                            .status-unknown { background-color: #e2e3e5; }
                        </style>
                    </head>
                    <body>
                        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                            <div class="container">
                                <a class="navbar-brand" href="/">Anti-Filter Bridge Monitor</a>
                            </div>
                        </nav>
                        
                        <div class="container mt-4">
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">Service Status</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-4">
                                                    <div id="status-card" class="card status-unknown">
                                                        <h3>Status: <span id="service-status">Unknown</span></h3>
                                                        <p id="status-message">Checking...</p>
                                                    </div>
                                                </div>
                                                <div class="col-md-8">
                                                    <div class="card">
                                                        <div class="card-body">
                                                            <h5 class="card-title">System Metrics</h5>
                                                            <div class="row">
                                                                <div class="col-md-6">
                                                                    <p>CPU: <span id="cpu-usage">-</span></p>
                                                                    <p>Memory: <span id="memory-usage">-</span></p>
                                                                </div>
                                                                <div class="col-md-6">
                                                                    <p>Disk: <span id="disk-usage">-</span></p>
                                                                    <p>Uptime: <span id="uptime">-</span></p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">CPU Usage</h5>
                                        </div>
                                        <div class="card-body">
                                            <canvas id="cpu-chart" height="200"></canvas>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">Memory Usage</h5>
                                        </div>
                                        <div class="card-body">
                                            <canvas id="memory-chart" height="200"></canvas>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">Recent Alerts</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="table-responsive">
                                                <table class="table table-striped" id="alerts-table">
                                                    <thead>
                                                        <tr>
                                                            <th>Time</th>
                                                            <th>Level</th>
                                                            <th>Message</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody id="alerts-body">
                                                        <tr>
                                                            <td colspan="3" class="text-center">Loading...</td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <script>
                            // Update the dashboard every 5 seconds
                            setInterval(updateDashboard, 5000);
                            
                            // Initial load
                            document.addEventListener('DOMContentLoaded', function() {
                                updateDashboard();
                            });
                            
                            // CPU Chart
                            const cpuCtx = document.getElementById('cpu-chart').getContext('2d');
                            const cpuChart = new Chart(cpuCtx, {
                                type: 'line',
                                data: {
                                    labels: [],
                                    datasets: [{
                                        label: 'CPU Usage %',
                                        data: [],
                                        borderColor: 'rgb(75, 192, 192)',
                                        tension: 0.1,
                                        fill: false
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    scales: {
                                        y: {
                                            beginAtZero: true,
                                            max: 100
                                        }
                                    }
                                }
                            });
                            
                            // Memory Chart
                            const memoryCtx = document.getElementById('memory-chart').getContext('2d');
                            const memoryChart = new Chart(memoryCtx, {
                                type: 'line',
                                data: {
                                    labels: [],
                                    datasets: [{
                                        label: 'Memory Usage %',
                                        data: [],
                                        borderColor: 'rgb(54, 162, 235)',
                                        tension: 0.1,
                                        fill: false
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    scales: {
                                        y: {
                                            beginAtZero: true,
                                            max: 100
                                        }
                                    }
                                }
                            });
                            
                            // Update the dashboard with fresh data
                            async function updateDashboard() {
                                try {
                                    const response = await fetch('/api/status');
                                    const data = await response.json();
                                    
                                    // Update service status
                                    const statusCard = document.getElementById('status-card');
                                    const statusText = document.getElementById('service-status');
                                    const statusMessage = document.getElementById('status-message');
                                    
                                    // Remove all status classes
                                    statusCard.className = 'card status-card status-' + data.service_status.service.toLowerCase();
                                    statusText.textContent = data.service_status.service.charAt(0).toUpperCase() + data.service_status.service.slice(1);
                                    
                                    if (data.service_status.service === 'running') {
                                        statusMessage.textContent = 'Service is running normally';
                                    } else if (data.service_status.service === 'degraded') {
                                        statusMessage.textContent = 'Service is running with issues';
                                    } else if (data.service_status.service === 'stopped') {
                                        statusMessage.textContent = 'Service is not running';
                                    } else {
                                        statusMessage.textContent = 'Status unknown';
                                    }
                                    
                                    // Update system metrics
                                    if (data.metrics) {
                                        document.getElementById('cpu-usage').textContent = data.metrics.cpu.percent.toFixed(1) + '%';
                                        document.getElementById('memory-usage').textContent = 
                                            (data.metrics.memory.used / (1024 * 1024 * 1024)).toFixed(2) + ' GB / ' + 
                                            (data.metrics.memory.total / (1024 * 1024 * 1024)).toFixed(2) + ' GB (' + 
                                            data.metrics.memory.percent.toFixed(1) + '%)';
                                        document.getElementById('disk-usage').textContent = 
                                            (data.metrics.disk.used / (1024 * 1024 * 1024)).toFixed(2) + ' GB / ' + 
                                            (data.metrics.disk.total / (1024 * 1024 * 1024)).toFixed(2) + ' GB (' + 
                                            data.metrics.disk.percent.toFixed(1) + '%)';
                                        
                                        // Update charts
                                        updateChart(cpuChart, data.metrics.cpu.percent);
                                        updateChart(memoryChart, data.metrics.memory.percent);
                                    }
                                    
                                    // Update uptime
                                    if (data.monitor_metrics && data.monitor_metrics.start_time) {
                                        const uptime = Math.floor((new Date() - new Date(data.monitor_metrics.start_time * 1000)) / 1000);
                                        const days = Math.floor(uptime / 86400);
                                        const hours = Math.floor((uptime % 86400) / 3600);
                                        const minutes = Math.floor((uptime % 3600) / 60);
                                        const seconds = uptime % 60;
                                        
                                        let uptimeStr = '';
                                        if (days > 0) uptimeStr += days + 'd ';
                                        if (hours > 0) uptimeStr += hours + 'h ';
                                        if (minutes > 0) uptimeStr += minutes + 'm ';
                                        uptimeStr += seconds + 's';
                                        
                                        document.getElementById('uptime').textContent = uptimeStr;
                                    }
                                    
                                    // Update alerts
                                    if (data.alerts && data.alerts.length > 0) {
                                        const alertsBody = document.getElementById('alerts-body');
                                        alertsBody.innerHTML = '';
                                        
                                        data.alerts.slice(0, 10).forEach(alert => {
                                            const row = document.createElement('tr');
                                            let levelClass = '';
                                            
                                            if (alert.level === 'critical') levelClass = 'table-danger';
                                            else if (alert.level === 'warning') levelClass = 'table-warning';
                                            else if (alert.level === 'info') levelClass = 'table-info';
                                            
                                            row.innerHTML = `
                                                <td>${new Date(alert.timestamp).toLocaleString()}</td>
                                                <td><span class="badge bg-${alert.level === 'critical' ? 'danger' : alert.level}">${alert.level.toUpperCase()}</span></td>
                                                <td>${alert.message}</td>
                                            `;
                                            
                                            alertsBody.appendChild(row);
                                        });
                                        
                                        if (data.alerts.length > 10) {
                                            const row = document.createElement('tr');
                                            row.innerHTML = `<td colspan="3" class="text-center">... and ${data.alerts.length - 10} more alerts</td>`;
                                            alertsBody.appendChild(row);
                                        }
                                    } else {
                                        document.getElementById('alerts-body').innerHTML = `
                                            <tr>
                                                <td colspan="3" class="text-center">No recent alerts</td>
                                            </tr>
                                        `;
                                    }
                                    
                                } catch (error) {
                                    console.error('Error updating dashboard:', error);
                                }
                            }
                            
                            // Helper function to update chart data
                            function updateChart(chart, newValue) {
                                const now = new Date().toLocaleTimeString();
                                
                                // Add new data point
                                chart.data.labels.push(now);
                                chart.data.datasets[0].data.push(newValue);
                                
                                // Keep only the last 20 data points
                                if (chart.data.labels.length > 20) {
                                    chart.data.labels.shift();
                                    chart.data.datasets[0].data.shift();
                                }
                                
                                // Update the chart
                                chart.update();
                            }
                        </script>
                    </body>
                    </html>
                    """)
            
            templates = Jinja2Templates(directory=templates_dir)
            
            # Basic Auth
            security = HTTPBasic()
            
            def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
                correct_username = self.config['web_interface'].get('username', 'admin')
                correct_password = self.config['web_interface'].get('password', 'admin123')
                
                if (credentials.username != correct_username or 
                    credentials.password != correct_password):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect username or password",
                        headers={"WWW-Authenticate": "Basic"},
                    )
                return credentials.username
            
            # API endpoints
            @app.get("/api/status")
            async def get_status():
                return {
                    "service_status": self.metrics.get('service_status', {}),
                    "metrics": self.metrics.get('performance_metrics', {}),
                    "alerts": self.alert_history[-10:],  # Last 10 alerts
                    "monitor_metrics": {
                        "start_time": self.metrics.get('start_time'),
                        "checks": self.metrics.get('checks', 0),
                        "alerts_triggered": self.metrics.get('alerts_triggered', 0),
                        "last_check": self.metrics.get('last_check')
                    }
                }
            
            @app.get("/api/metrics")
            async def get_metrics():
                return self.metrics.get('performance_metrics', {})
            
            @app.get("/api/alerts")
            async def get_alerts(limit: int = 10):
                return self.alert_history[-limit:]
            
            @app.get("/api/restart")
            async def restart_service():
                # This is a placeholder - in a real implementation, you would restart the service
                return {"status": "success", "message": "Restart command sent"}
            
            # Web interface routes
            @app.get("/", response_class=HTMLResponse)
            async def read_root(request: Request, username: str = Depends(get_current_username)):
                return templates.TemplateResponse("index.html", {"request": request})
            
            import uvicorn
            
            # Start the web server
            host = self.config['web_interface'].get('host', '127.0.0.1')
            port = int(self.config['web_interface'].get('port', 8080))
            
            logger.info(f"Starting web interface on http://{host}:{port}")
            
            config = uvicorn.Config(
                app,
                host=host,
                port=port,
                log_level="info"
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except ImportError as e:
            logger.error(f"Failed to start web interface. Required packages not found: {e}")
            logger.info("Install required packages with: pip install fastapi uvicorn python-multipart jinja2")
        except Exception as e:
            logger.error(f"Error in web interface: {e}")
    
    async def run_checks(self):
        """Run monitoring checks in a loop."""
        self.running = True
        check_interval = int(self.config['monitor'].get('check_interval', 60))
        
        logger.info("Starting Anti-Filter Bridge monitor...")
        
        # Start web interface in the background
        import asyncio
        web_interface_task = asyncio.create_task(self.start_web_interface())
        
        try:
            while self.running:
                try:
                    # Run checks
                    status = await self.check_service_status()
                    metrics = await self.check_system_metrics()
                    alerts = await self.check_alerts(status, metrics)
                    
                    # Log status
                    logger.info(f"Service status: {status['service'].upper()}")
                    logger.debug(f"Metrics: {json.dumps(metrics, indent=2)}")
                    
                    if alerts:
                        for alert in alerts:
                            logger.warning(f"ALERT: {alert['message']}")
                    
                except Exception as e:
                    logger.error(f"Error during monitoring check: {e}", exc_info=True)
                
                # Wait for the next check
                await asyncio.sleep(check_interval)
                
        except asyncio.CancelledError:
            logger.info("Monitoring task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in monitoring loop: {e}", exc_info=True)
        finally:
            self.running = False
            
            # Cancel the web interface task
            if not web_interface_task.done():
                web_interface_task.cancel()
                try:
                    await web_interface_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Monitoring stopped")
    
    def start(self):
        """Start the monitor."""
        try:
            asyncio.run(self.run_checks())
        except KeyboardInterrupt:
            logger.info("Shutdown requested. Stopping monitor...")
        except Exception as e:
            logger.error(f"Error in monitor: {e}", exc_info=True)
            sys.exit(1)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Anti-Filter Bridge Monitor')
    
    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file',
        default=None
    )
    
    parser.add_argument(
        '--check-interval',
        help='Interval between checks in seconds',
        type=int,
        default=None
    )
    
    parser.add_argument(
        '--web-interface',
        help='Enable/disable web interface',
        type=lambda x: x.lower() in ('true', 'yes', '1'),
        default=None
    )
    
    parser.add_argument(
        '--web-host',
        help='Web interface host',
        default=None
    )
    
    parser.add_argument(
        '--web-port',
        help='Web interface port',
        type=int,
        default=None
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the monitor."""
    args = parse_arguments()
    
    # Create and configure monitor
    monitor = AFBMonitor(args.config)
    
    # Override config with command-line arguments
    if args.check_interval is not None:
        monitor.config['monitor']['check_interval'] = str(args.check_interval)
    
    if args.web_interface is not None:
        monitor.config['web_interface']['enabled'] = 'true' if args.web_interface else 'false'
    
    if args.web_host is not None:
        monitor.config['web_interface']['host'] = args.web_host
    
    if args.web_port is not None:
        monitor.config['web_interface']['port'] = str(args.web_port)
    
    # Start monitoring
    monitor.start()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
