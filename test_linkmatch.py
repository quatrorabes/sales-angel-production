#!/usr/bin/env python3
"""Test LinkMatch Pro Integration"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import LinkMatch integration
try:
    from linkmatch_pro_integration import get_linkmatch_ai_insights
    print("✅ LinkMatch module imported successfully!")
    
    async def test_linkmatch():
        """Test the LinkMatch integration"""
        try:
            insights = await get_linkmatch_ai_insights('contact-123')
            print("✅ LinkMatch insights retrieved:")
            print(insights)
        except Exception as e:
            print(f"❌ LinkMatch test failed: {e}")
    
    # Run the async function
    asyncio.run(test_linkmatch())
    
except ImportError as e:
    print(f"❌ Failed to import LinkMatch module: {e}")
    print("\nMake sure the file exists and has the right structure")
