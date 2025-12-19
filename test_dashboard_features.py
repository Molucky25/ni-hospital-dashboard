"""
Test script to demonstrate the new dashboard features:
1. Logo display (corner + watermark)
2. 24-hour trend sparkline
3. Hospital trend indicators (↑ rising / ↓ improving)
"""

import asyncio
from generate_dashboard_image import generate_dashboard_image
from datetime import datetime, timezone

# Sample hospital data
sample_rows = [
    {"hospital": "Altnagelvin Area Hospital Emergency Department", "wait_mins": 317, "status": "Open"},
    {"hospital": "Royal Victoria Hospital Emergency Department", "wait_mins": 281, "status": "Open"},
    {"hospital": "Ulster Hospital Emergency Department", "wait_mins": 238, "status": "Open"},
    {"hospital": "Mater Hospital Emergency Department", "wait_mins": 220, "status": "Open"},
    {"hospital": "Antrim Area Hospital Emergency Department", "wait_mins": 162, "status": "Open"},
    {"hospital": "Craigavon Area Hospital Emergency Department", "wait_mins": 157, "status": "Open"},
    {"hospital": "Causeway Hospital Emergency Department", "wait_mins": 152, "status": "Open"},
    {"hospital": "South West Acute Hospital Emergency Department", "wait_mins": 131, "status": "Open"},
    {"hospital": "Royal Children's Hospital Emergency Department", "wait_mins": 119, "status": "Open"},
    {"hospital": "Daisy Hill Hospital Emergency Department", "wait_mins": 86, "status": "Open"},
]


async def main():
    """Test the dashboard with new features."""
    
    print("=" * 60)
    print("Testing Dashboard Features")
    print("=" * 60)
    
    timestamp = datetime.now(timezone.utc).astimezone().strftime("%I:%M %p, %a %d %b %Y")
    
    print("\n✅ Feature 1: Logo Display")
    print("   - Logo in top-right corner")
    print("   - Subtle watermark in background")
    print("   - Logo path: C:\\Users\\m0luc\\OneDrive\\Documents\\Desktop\\hospital wait\\NIERV Logo.jpg")
    
    print("\n✅ Feature 2: 24-Hour Trend Tracking")
    print("   - Historical data saved to: hospital_wait_trends.jsonl")
    print("   - Sparkline graph shows hourly averages")
    print("   - Trend line color: Red (rising) / Green (improving)")
    
    print("\n✅ Feature 3: Hospital Trend Indicators")
    print("   - ↑ rising: Wait time increased by >15 minutes")
    print("   - ↓ improving: Wait time decreased by >15 minutes")
    print("   - Based on comparison with 4-8 hours ago")
    
    print("\n📊 Generating dashboard image...")
    
    # Generate the dashboard
    await generate_dashboard_image(
        sample_rows, 
        timestamp,
        output_path="test_dashboard_with_features.png"
    )
    
    print("\n✅ Dashboard generated: test_dashboard_with_features.png")
    print("\n📝 How it works:")
    print("   1. First run: Creates trend file, no sparkline (need history)")
    print("   2. Subsequent runs: Builds trend data over time")
    print("   3. After 24 hours: Full sparkline with 24 data points")
    print("   4. Hospital trends: Compare current vs 4-8 hours ago")
    
    print("\n💡 Tips:")
    print("   - Run the monitoring script regularly to build trend data")
    print("   - Trend indicators appear when change is >15 minutes")
    print("   - Historical data auto-cleans after 7 days")
    print("   - Logo watermark opacity is 5% for subtle branding")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
