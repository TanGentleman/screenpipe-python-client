import asyncio
from src.core.screenpipe import ScreenpipeClient

async def check_and_search():
    async with ScreenpipeClient() as client:
        # Create all tasks at once
        tasks = [
            client._make_request_async("GET", "health"),
            client._make_request_async("GET", "search", params={
                "query": "folake",
                "limit": 1,
                "content_type": "audio"
            }),
            client._make_request_async("GET", "search", params={
                "query": "manit",
                "limit": 1,
                "content_type": "audio"
            }),
            client._make_request_async("GET", "search", params={
                "query": "",
                "limit": 3,
                "content_type": "audio"
            })
        ]
        
        try:
            results = await asyncio.gather(*tasks)
            
            # Process results
            health_check, search1, search2, search3 = results
            
            if health_check:
                print("Health check result:", health_check)
            
            if search1:
                print("First search results:", search1)
            
            if search2:
                print("Second search results:", search2)
                
            if search3:
                print("Third search results:", search3)
                
            return results
            
        except Exception as e:
            print(f"Error during requests: {e}")
            return None

if __name__ == "__main__":
    results = asyncio.run(check_and_search())

