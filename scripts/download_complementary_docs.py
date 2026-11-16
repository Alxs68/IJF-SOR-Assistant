
import os
import urllib.request
import hashlib

dest_dir = os.path.join('data', 'raw', 'complementary')
os.makedirs(dest_dir, exist_ok=True)

docs = [
    {
        'id': 'DOC-DIS-2023',
        'filename': 'IJF_Disciplinary_Code_2023_05_04.pdf',
        'url': 'https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2023/05/IJF_Disciplinary_Code_-_04_05_-1685023168.pdf',
        'title': 'IJF Disciplinary Code (04 May 2023)'
    },
    {
        'id': 'DOC-ETH-2023',
        'filename': 'IJF_Code_of_Ethics_2023_02_27.pdf',
        'url': 'https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2024/07/IJF_Code_of_Ethics_27_02_2023_-1722455092.pdf',
        'title': 'IJF Code of Ethics (27 February 2023)'
    },
    {
        'id': 'DOC-QSY-2026',
        'filename': 'IJF_LA28_Olympic_Qualification_System_2026_05_12.pdf',
        'url': 'https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/06/JUD-LA28-Qualification-System--1781162989.pdf',
        'title': 'LA28 Olympic Games Qualification System Judo (12 May 2026)'
    }
]

for doc in docs:
    filepath = os.path.join(dest_dir, doc['filename'])
    title = doc['title']
    print(f'Downloading {title}...')
    req = urllib.request.Request(doc['url'], headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        content = resp.read()
    with open(filepath, 'wb') as f:
        f.write(content)
    h = hashlib.sha256(content).hexdigest()
    size = len(content)
    print(f'Saved: {filepath} ({size} bytes, sha256={h})')
