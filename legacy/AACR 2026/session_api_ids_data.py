import requests
import json
import time

# Configuration
base_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9',
    'Backpack': 'fc1c7fbf-ad1b-4394-ad77-6a0275642b11',
    'Connection': 'keep-alive',
    'Host': 'www.abstractsonline.com',
    'Referer': 'https://www.abstractsonline.com/pp8/',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Cookie': 'fpestid=3sNRbRe-U70wnAfBWdGrsjQkTKJAZZj7MmeWl-Adb-zEneATqW8WX9gebr3wWakX0A5QeQ; corpRollup_ga=GA1.1.1766169932.1753237027; _ga_4699REKRC5=GS2.1.s1764839823$o21$g0$t1764839823$j60$l0$h0; corpRollup_ga_EQ32SZ84M3=GS2.1.s1764839823$o21$g0$t1764839823$j60$l0$h0; _ga_2V8VW4Y237=GS2.1.s1769220975$o2$g1$t1769235014$j59$l0$h0; _ga_DR4SQFLWZ1=GS2.1.s1773230651$o58$g0$t1773230651$j60$l0$h0; _ga=GA1.2.1766169932.1753237027; _gid=GA1.2.1998292806.1773722582; backpack=fc1c7fbf-ad1b-4394-ad77-6a0275642b11; backpackExpiration=Wed%2C%2018%20Mar%202026%2017%3A38%3A36; _ga_J6BCLJPMPE=GS2.2.s1773801172$o49$g0$t1773801172$j60$l0$h0; AWSALB=upiCmvYNRMbs5ROpnL1hIqT7PIn2yzVAIRBil/T9EDTQOVObFxo0Oh83aqSKDcbIvuIXhpxkOHCgnXH2XpLg+YksAumyALlZGaA6DOqHsZGmBa7/Jtj3LX15cE9w; AWSALBCORS=upiCmvYNRMbs5ROpnL1hIqT7PIn2yzVAIRBil/T9EDTQOVObFxo0Oh83aqSKDcbIvuIXhpxkOHCgnXH2XpLg+YksAumyALlZGaA6DOqHsZGmBa7/Jtj3LX15cE9w'
}

# Define URLs for each date with their pagination info
url_configs = [
    # April 17 - 2 pages
    {'base_url': 'https://www.abstractsonline.com/oe3/Program/21436/Search/7/Results', 'total_pages': 2},
    # April 18 - 6 pages
    {'base_url': 'https://www.abstractsonline.com/oe3/Program/21436/Search/9/Results', 'total_pages': 6},
    # April 19 - 12 pages
    {'base_url': 'https://www.abstractsonline.com/oe3/Program/21436/Search/10/Results', 'total_pages': 13},
    # April 20 - 20 pages
    {'base_url': 'https://www.abstractsonline.com/oe3/Program/21436/Search/11/Results', 'total_pages': 20},
    # April 21 - 19 pages
    {'base_url': 'https://www.abstractsonline.com/oe3/Program/21436/Search/13/Results', 'total_pages': 19},
    # April 22 - 6 pages
    {'base_url': 'https://www.abstractsonline.com/oe3/Program/21436/Search/8/Results', 'total_pages': 6}
]

# Build complete URL list with all pages
url_list = []
for config in url_configs:
    for page in range(1, config['total_pages'] + 1):
        url = f"{config['base_url']}?page={page}&pagesize=10&sort=1&order=asc"
        url_list.append(url)

output_file = "session_api_data.json"

# Create session and set headers
session = requests.Session()
session.headers.update(base_headers)

if __name__ == '__main__':
    results = []
    
    for i, url in enumerate(url_list):
        print(f"{i+1}/{len(url_list)} - {url}")
        
        try:
            r = session.get(url)
            print(f"Status code: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                results.append(data)
                print(f"  → Data retrieved successfully")
            else:
                print(f"  → Failed to retrieve data")
                
        except Exception as e:
            print(f"  → Error: {e}")
        
        # Be polite to the server
        time.sleep(1)
    
    # Save all raw JSON data to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"\nCollection complete!")
    print(f"Total pages collected: {len(results)}")
    print(f"Data saved to: {output_file}")