#!/usr/bin/env python3
"""
Monitoring script for Anti-Filter Bridge deployments.
This script monitors the health and performance of deployed instances.
"""
import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional

class DeploymentMonitor:
    def __init__(self):
        self.deployments = {
            'railway': 'https://adventurous-youth-production.up.railway.app',
            'heroku': 'https://anti-filter-bridge.herokuapp.com',
            'render': 'https://anti-filter-bridge.onrender.com'
        }
        self.results = {}
    
    async def check_health(self, name: str, url: str) -> Dict:
        """Check the health of a deployment."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                start_time = time.time()
                
                # Try to connect to the WebSocket endpoint
                ws_url = url.replace('https://', 'wss://').replace('http://', 'ws://')
                ws_url += ':8080' if ':8080' not in ws_url else ''
                
                try:
                    async with session.ws_connect(ws_url) as ws:
                        await ws.close()
                        ws_status = "✅ Connected"
                except Exception as e:
                    ws_status = f"❌ WebSocket Error: {str(e)[:50]}"
                
                # Try HTTP health check
                try:
                    async with session.get(f"{url}/status") as response:
                        if response.status == 200:
                            http_status = "✅ HTTP OK"
                            data = await response.json()
                        else:
                            http_status = f"❌ HTTP {response.status}"
                            data = {}
                except Exception as e:
                    http_status = f"❌ HTTP Error: {str(e)[:50]}"
                    data = {}
                
                response_time = (time.time() - start_time) * 1000
                
                return {
                    'name': name,
                    'url': url,
                    'status': 'healthy' if '✅' in ws_status and '✅' in http_status else 'unhealthy',
                    'websocket': ws_status,
                    'http': http_status,
                    'response_time_ms': round(response_time, 2),
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }
                
        except Exception as e:
            return {
                'name': name,
                'url': url,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def monitor_all(self):
        """Monitor all deployments."""
        print("🔍 Monitoring Anti-Filter Bridge Deployments...")
        print("=" * 60)
        
        tasks = []
        for name, url in self.deployments.items():
            tasks.append(self.check_health(name, url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"❌ Error monitoring: {result}")
                continue
                
            self.results[result['name']] = result
            
            # Print status
            status_icon = "✅" if result['status'] == 'healthy' else "❌"
            print(f"{status_icon} {result['name'].upper()}")
            print(f"   URL: {result['url']}")
            print(f"   Status: {result['status']}")
            print(f"   WebSocket: {result.get('websocket', 'N/A')}")
            print(f"   HTTP: {result.get('http', 'N/A')}")
            print(f"   Response Time: {result.get('response_time_ms', 'N/A')}ms")
            print()
    
    def generate_report(self):
        """Generate a monitoring report."""
        healthy_count = sum(1 for r in self.results.values() if r['status'] == 'healthy')
        total_count = len(self.results)
        
        print("📊 Monitoring Report")
        print("=" * 30)
        print(f"Total Deployments: {total_count}")
        print(f"Healthy: {healthy_count}")
        print(f"Unhealthy: {total_count - healthy_count}")
        print(f"Success Rate: {(healthy_count/total_count)*100:.1f}%" if total_count > 0 else "N/A")
        print()
        
        # Save results to file
        with open('monitoring_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print("📁 Results saved to monitoring_results.json")
    
    async def continuous_monitor(self, interval: int = 60):
        """Continuously monitor deployments."""
        print(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                await self.monitor_all()
                self.generate_report()
                print(f"⏰ Next check in {interval} seconds...")
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")

async def main():
    """Main function."""
    monitor = DeploymentMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        await monitor.continuous_monitor(interval)
    else:
        await monitor.monitor_all()
        monitor.generate_report()

if __name__ == "__main__":
    asyncio.run(main())
