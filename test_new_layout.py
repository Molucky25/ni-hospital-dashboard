"""
Quick test for the new dashboard layout with:
- Table on left, stats on right
- All 10 hospitals visible
- Larger text for readability
- Logo properly displaying
"""

import asyncio
from generate_dashboard_image import generate_dashboard_image
from datetime import datetime, timezone

# Sample hospital data - all 10 hospitals
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
    print("=" * 60)
    print("Testing New Dashboard Layout")
    print("=" * 60)
    
    print("\n✅ New Features:")
    print("   - Table on left (narrow width)")
    print("   - Stats boxes on right (fills space)")
    print("   - All 10 hospitals visible")
    print("   - Larger text (better readability)")
    print("   - Logo embedded as base64 (should display)")
    print("   - Footer text increased to 14px")
    
    timestamp = datetime.now(timezone.utc).astimezone().strftime("%I:%M %p, %a %d %b %Y")
    
    print("\n📊 Generating dashboard...")
    
    await generate_dashboard_image(
        sample_rows, 
        timestamp,
        output_path="test_new_layout.png"
    )
    
    print("\n✅ Dashboard generated: test_new_layout.png")
    print("\n💡 Check the image - all 10 hospitals should be visible!")
    print("   Logo should display in top-right corner.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
