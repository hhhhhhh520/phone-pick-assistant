import requests
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

r = requests.get('https://www.antutu.com/class_100032/index.htm', headers=headers, timeout=15)
r.encoding = 'utf-8'
text = r.text

# Find review links
links = re.findall(r'href="(/doc/[^"]+)"', text)
print('Review links found:', len(links))
for l in links[:10]:
    print(' ', l)

# Find evaluation keywords
ratings = re.findall(r'(优|缺|评|分|星|推荐|体验|续航|拍照|游戏|性能|优点|缺点)', text)
print('\nEvaluation keywords:', list(set(ratings)))

# Strip HTML and show clean text
clean = re.sub(r'<[^>]+>', ' ', text)
clean = re.sub(r'\s+', ' ', clean).strip()
print('\n=== Clean text (first 2000) ===')
print(clean[:2000])
