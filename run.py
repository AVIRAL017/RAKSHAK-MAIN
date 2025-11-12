#!/usr/bin/env python3
"""
SafeRoute Navigator v2.0 - Application Runner
Simple script to run the complete SafeRoute Navigator application.
"""

import os
import sys
import logging
from datetime import datetime

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the Flask app factory
from app import create_app

def setup_logging():
    """Setup application logging."""
    log_level = logging.INFO
    if '--debug' in sys.argv:
        log_level = logging.DEBUG
        
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'saferoute_{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )

def print_banner():
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    🛡️  SafeRoute Navigator v2.0                          ║
    ║    AI-Powered Route Safety Intelligence                   ║
    ║                                                           ║
    ║    🌟 Real-time weather integration                       ║
    ║    🤖 ML-powered hotspot predictions                      ║
    ║    🗺️  Interactive safety mapping                         ║
    ║    📱 Responsive design                                   ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"    🚀 Starting SafeRoute Navigator...")
    print(f"    📍 Server will be available at: http://localhost:5000")
    print(f"    🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    📝 Logs: saferoute_{datetime.now().strftime('%Y%m%d')}.log")
    print()

def main():
    """Main application runner."""
    # Parse command line arguments
    debug_mode = '--debug' in sys.argv
    port = 5000
    host = '0.0.0.0'
    
    # Check for custom port
    for arg in sys.argv:
        if arg.startswith('--port='):
            port = int(arg.split('=')[1])
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Print banner
    print_banner()
    
    try:
        logger.info("SafeRoute Navigator v2.0 starting...")
        logger.info(f"Debug mode: {debug_mode}")
        logger.info(f"Host: {host}, Port: {port}")
        
        # Check if OpenWeatherMap API key is configured
        if not os.getenv('OPENWEATHER_API_KEY'):
            logger.info("OpenWeatherMap API key not found in environment, using default from weather service")
        
        # Create the Flask application
        app = create_app()
        
        # Start the Flask application
        app.run(
            host=host,
            port=port,
            debug=debug_mode,
            threaded=True,
            use_reloader=False  # Disable reloader to avoid duplicate startup messages
        )
        
    except KeyboardInterrupt:
        logger.info("SafeRoute Navigator shutdown by user")
        print("\n    👋 SafeRoute Navigator stopped safely. Drive safe!")
        
    except Exception as e:
        logger.error(f"SafeRoute Navigator failed to start: {str(e)}")
        print(f"\n    ❌ Failed to start: {str(e)}")
        print("    💡 Try running with --debug for more information")
        sys.exit(1)

if __name__ == "__main__":
    main()