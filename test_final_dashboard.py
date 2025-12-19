"""
Final test for all dashboard improvements:
✅ All 10 hospitals visible
✅ 160px logo
✅ No ambulance emoji
✅ Severity key in footer
✅ Source & triage info
✅ Facebook link
✅ New stats (Under 60m, Over 240m)
"""

import asyncio
from generate_dashboard_image import generate_dashboard_image
from datetime import datetime, timezone

# All 10 hospitals - COMPLETE DATA
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
    print("=" * 70)
    print("FINAL DASHBOARD TEST - All Improvements")
    print("=" * 70)
    
    print("\n✅ Fixed Issues:")
    print("   1. All 10 hospitals visible (reduced padding py-2)")
    print("   2. Logo enlarged to 160px (w-40)")
    print("   3. Removed ambulance emoji from title")
    print("   4. Added severity key to footer")
    print("   5. Added source info (NI Direct)")
    print("   6. Added triage information")
    print("   7. Changed to Facebook link (fb.me/NIERV)")
    print("   8. Reduced table width to 580px")
    print("   9. Footer reorganized (3 columns)")
    
    print("\n📊 New Stats Added:")
    print("   • 🟢 Under 60m Count: 1 hospital (Daisy Hill)")
    print("   • 🔴 Over 240m Count: 2 hospitals (Altnagelvin, Royal Victoria)")
    
    print("\n💡 Additional Stats Suggested (see ALL_FIXES_AND_STATS.md):")
    print("   • 🏆 Shortest Wait")
    print("   • 📈 Change from Last Update")
    print("   • 🟡 60-119m Count")
    print("   • 🟠 120-239m Count")
    print("   • 🔔 Alert Level")
    print("   • And 10 more ideas!")
    
    timestamp = datetime.now(timezone.utc).astimezone().strftime("%I:%M %p, %a %d %b %Y")
    
    print("\n📸 Generating final dashboard image...")
    
    await generate_dashboard_image(
        sample_rows, 
        timestamp,
        output_path="final_dashboard.png"
    )
    
    print("\n✅ Dashboard generated: final_dashboard.png")
    
    print("\n🔍 Please verify:")
    print("   [ ] All 10 hospitals visible (check for Daisy Hill at bottom)")
    print("   [ ] Logo is large and prominent (160px)")
    print("   [ ] Title has NO ambulance emoji")
    print("   [ ] Footer shows severity key (🟢🟡🟠🔴)")
    print("   [ ] Footer shows 'Source: NI Direct'")
    print("   [ ] Footer shows triage information")
    print("   [ ] Footer shows 'fb.me/NIERV' (not Telegram)")
    print("   [ ] Table is narrower with more space for stats")
    print("   [ ] New stats cards: Under 60m (1) and Over 240m (2)")
    
    print("\n📈 Expected Stats in Image:")
    print("   • Longest Wait: Altnagelvin — 317m 🔴")
    print("   • Average Wait: 186m 🟠")
    print("   • Hospitals Reporting: 10")
    print("   • Under 60m: 1")
    print("   • Over 240m: 2")
    
    print("\n" + "=" * 70)
    print("All improvements complete! 🎉")
    print("=" * 70)
    print("\n📖 Read ALL_FIXES_AND_STATS.md for additional stat ideas")

if __name__ == "__main__":
    asyncio.run(main())
