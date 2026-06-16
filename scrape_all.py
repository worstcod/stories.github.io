import subprocess
import re
import json
import os
import html
import time
import urllib.parse
from bs4 import BeautifulSoup

# Target directory
STORIES_DIR = "stories"
if not os.path.exists(STORIES_DIR):
    os.makedirs(STORIES_DIR)

# HTML cleaner to extract clean formatted prose
def clean_html(html_str):
    # Remove styles & scripts
    html_str = re.sub(r'<style[^>]*>.*?</style>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
    html_str = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
    # Replace block level elements and line breaks with newline markers
    html_str = re.sub(r'</?(p|div|br|h1|h2|h3|li|tr|pre|dt|dd)[^>]*>', '\n', html_str, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    clean = re.sub(r'<[^>]+>', '', html_str)
    # Decode HTML entities
    clean = html.unescape(clean)
    # Clean up standard typographer quotes and dashes
    clean = clean.replace('\xa0', ' ')
    clean = clean.replace('\u201d', '"').replace('\u201c', '"')
    clean = clean.replace('\u2019', "'").replace('\u2018', "'")
    clean = clean.replace('\u2013', '-').replace('\u2014', '--')
    
    # Collapse multiple consecutive empty lines
    clean = re.sub(r'\r\n', '\n', clean)
    clean = re.sub(r'\n\s*\n', '\n\n', clean)
    
    return clean.strip()

# Robust curl fetch helper with compression, SSL bypass, and retry logic
def fetch_with_curl(url, max_retries=3):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    print(f"Fetching: {url}")
    
    for attempt in range(1, max_retries + 1):
        # Try 1: normal curl with compression
        cmd1 = ["C:\\Windows\\System32\\curl.exe", "--compressed", "-s", "-A", ua, url]
        res = subprocess.run(cmd1, capture_output=True)
        if res.returncode == 0 and len(res.stdout) > 500:
            return res.stdout.decode('utf-8', errors='ignore')
            
        # Try 2: with SSL revocation and certificate checks bypassed
        cmd2 = ["C:\\Windows\\System32\\curl.exe", "-k", "--ssl-no-revoke", "--compressed", "-s", "-A", ua, url]
        res2 = subprocess.run(cmd2, capture_output=True)
        if res2.returncode == 0 and len(res2.stdout) > 500:
            return res2.stdout.decode('utf-8', errors='ignore')
            
        print(f"  [RETRY] Attempt {attempt} failed for {url}. Code1: {res.returncode}, Code2: {res2.returncode}. Retrying in {attempt * 2}s...")
        time.sleep(attempt * 2)
        
    print(f"  [ERROR] Failed to fetch {url} after {max_retries} attempts.")
    return ""

# Categorize story based on word count
def assign_category_by_length(content):
    words = len(content.split())
    if words < 150:
        return "flash"
    elif words <= 500:
        return "mid"
    else:
        return "deep"

# Normalize text for similarity matching
def clean_text_for_sim(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

# Deduplicate stories by comparing normalized titles and Jaccard word overlaps
def deduplicate_stories(all_stories, tag_name="Stories"):
    print(f"\nRunning {tag_name} deduplication...")
    unique_stories = []
    
    for s in all_stories:
        content_norm = clean_text_for_sim(s["content"])
        title_norm = clean_text_for_sim(s["title"])
        
        is_dup = False
        for u in unique_stories:
            u_content_norm = clean_text_for_sim(u["content"])
            u_title_norm = clean_text_for_sim(u["title"])
            
            # 1. Exact title check
            if title_norm == u_title_norm and title_norm:
                is_dup = True
                print(f"  [DUP BY TITLE] '{s['title']}' ({s.get('source', 'Unknown')}) duplicate of '{u['title']}' ({u.get('source', 'Unknown')})")
                # Retain the version with the longer content body
                if len(s["content"]) > len(u["content"]):
                    u["content"] = s["content"]
                    u["id"] = s["id"]
                break
                
            # 2. Content similarity check (Jaccard and Containment ratios)
            words_s = set(re.findall(r'[a-z0-9]+', s["content"].lower()))
            words_u = set(re.findall(r'[a-z0-9]+', u["content"].lower()))
            
            if not words_s or not words_u:
                continue
                
            intersection = words_s.intersection(words_u)
            union = words_s.union(words_u)
            
            similarity = len(intersection) / len(union)
            containment_s = len(intersection) / len(words_s)
            containment_u = len(intersection) / len(words_u)
            
            if similarity > 0.65 or containment_s > 0.85 or containment_u > 0.85:
                is_dup = True
                print(f"  [DUP BY SIMILARITY {similarity:.2f}] '{s['title']}' ({s.get('source', 'Unknown')}) duplicate of '{u['title']}' ({u.get('source', 'Unknown')})")
                # Retain the version with the longer content body
                if len(s["content"]) > len(u["content"]):
                    u["content"] = s["content"]
                    u["id"] = s["id"]
                break
                
        if not is_dup:
            # Clean up the helper 'source' key before exporting
            s_out = s.copy()
            if "source" in s_out:
                del s_out["source"]
            unique_stories.append(s_out)
            
    print(f"Deduplication complete. Retained {len(unique_stories)} unique stories out of {len(all_stories)} total.\n")
    return unique_stories

# ----------------- 1. SCRAPE OSHO STORIES -----------------
def scrape_osho():
    print("\n--- SCRAPING OSHO STORIES ---")
    stories = []
    
    # Preloaded manual entries
    stories.append({
        "id": "osho-empty-boat",
        "title": "The Empty Boat",
        "author": "Osho",
        "category": "mid",
        "content": "Chuang Tzu tells the story of a man who was crossing a river in a boat. Another boat, which was empty, came drifting downstream and bumped into his boat. Even though he was a man of quick temper, he did not get angry. He simply steered his boat out of the way.\n\nThen he saw another boat coming down, and in this boat there was a man. He began to shout at him, telling him to steer clear. When the man did not hear, he shouted again, and began to curse.\n\nAll because there was a person in that boat! If the boat had been empty, he would not have shouted, he would not have been angry.\n\nSo it is with the world. If you can empty your own boat when crossing the river of the world, no one will oppose you, no one will seek to harm you.\n\nThe anger of others is always because your boat is not empty—because you are there, your ego is there, asserting itself. If you empty your boat, who can collide with you? If you are a nobody, who can insult you? Empty your boat, and let the world drift past."
    })
    stories.append({
        "id": "osho-lost-key",
        "title": "Mulla Nasruddin and the Lost Key",
        "author": "Osho",
        "category": "mid",
        "content": "One evening, Mulla Nasruddin was seen by his neighbors searching frantically for something on the ground outside his house, right under the streetlamp.\n\n\"What have you lost, Mulla?\" they asked.\n\"My key,\" replied Mulla.\n\nThe neighbors, being helpful, knelt down to join him in the search. After searching for an hour under the bright streetlamp without success, one neighbor asked, \"Mulla, are you sure you lost it here?\"\n\n\"Oh, no,\" Mulla answered, pointing toward the dark alleyways. \"I lost it inside my house, near my bed.\"\n\nThe neighbor was astounded. \"Then why on earth are you searching for it out here under the streetlamp?\"\n\nMulla smiled and said, \"Because there is light here, and my house is pitch dark!\"\n\nMoral: This is the state of human consciousness. We search for happiness, peace, and love outside in the world, simply because it is easier to look outside. But we lost it inside ourselves. Go inside, even if it is dark initially."
    })
    stories.append({
        "id": "osho-this-too-shall-pass",
        "title": "This Too Shall Pass",
        "author": "Osho",
        "category": "mid",
        "content": "A powerful king once gathered all the wise men in his court and said, \"I want you to make me a ring. Engrave a message on it that will comfort me in times of deep sorrow, and humble me in times of great joy. It must be short so it can fit on a small ring.\"\n\nThe wise men debated and searched through scriptures but could not find such a message. \n\nHowever, an old advisor in the court approached the king. He handed him a small paper containing a hidden message, saying, \"Do not read it now. Keep it inside the ring, and only open it when you are in absolute despair.\"\n\nMonths later, the kingdom was invaded. The king was defeated, his army fled, and he was forced to ride into the forest with enemies chasing him. He reached a dead end at the edge of a steep cliff. He could hear the horses of the enemy approaching. He felt complete despair.\n\nSuddenly, he remembered the ring. He took it off, pulled out the paper, and read the message: \"This too shall pass.\"\n\nUpon reading it, a deep silence fell upon him. The sound of the enemies faded; they must have taken a wrong turn in the forest. He sat in peace.\n\nYears later, he gathered his kingdom again, defeated his enemies, and was celebrated with great pomp. He felt proud and victorious. The old advisor came to him and said, \"My King, read the message again.\"\n\nThe king read it: \"This too shall pass.\"\nHis pride vanished, his heart softened, and he understood the transient nature of all things in life."
    })

    try:
        post_links = []
        for page_num in range(1, 13):
            try:
                page_url = f"https://oshostories.wordpress.com/page/{page_num}/"
                page_html = fetch_with_curl(page_url)
                if not page_html:
                    continue
                links = re.findall(r'href=["\'](https://oshostories\.wordpress\.com/\d{4}/\d{2}/\d{2}/[^"\']+)["\']', page_html)
                post_links.extend(links)
            except Exception as page_e:
                print(f"Error fetching Osho page {page_num}: {page_e}")
                
        post_links = list(set(post_links))
        print(f"Found {len(post_links)} unique post links on Osho Stories blog.")
        
        scraped_count = 0
        for link in post_links:
            if scraped_count >= 80:
                break
            try:
                post_html = fetch_with_curl(link)
                if not post_html:
                    continue
                
                title_match = re.search(r'<h1[^>]*class="[^"]*entry-title[^"]*"[^>]*>(.*?)</h1>', post_html, re.IGNORECASE)
                if not title_match:
                    title_match = re.search(r'<title>(.*?)</title>', post_html, re.IGNORECASE)
                
                content_match = re.search(r'<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>', post_html, re.DOTALL | re.IGNORECASE)
                
                if title_match and content_match:
                    title = clean_html(title_match.group(1))
                    title = re.sub(r'\s*\|\s*Osho\s*Stories.*', '', title, flags=re.IGNORECASE).strip()
                    
                    content_raw = content_match.group(1)
                    story_text = clean_html(content_raw)
                    
                    if len(story_text) < 150:
                        continue
                        
                    story_id = "osho-scraped-" + title.lower().replace(" ", "-").replace("?", "").replace(",", "").replace("!", "")
                    story_id = re.sub(r'[^a-z0-9\-]', '', story_id)[:40]
                    
                    stories.append({
                        "id": story_id,
                        "title": title,
                        "author": "Osho",
                        "category": "mid",
                        "content": story_text
                    })
                    scraped_count += 1
                    print(f"Scraped Osho post {scraped_count}: {title}")
            except Exception as inner_e:
                print(f"Error fetching Osho post {link}: {inner_e}")
                
    except Exception as e:
        print(f"Error scraping Osho: {e}")
        
    return stories

# ----------------- 2. SCRAPE AESOP'S FABLES -----------------
def scrape_aesop():
    print("\n--- SCRAPING AESOP'S FABLES ---")
    stories = []
    
    stories.append({
        "id": "aesop-crow-pitcher",
        "title": "The Crow and the Pitcher",
        "author": "Aesop",
        "category": "mid",
        "content": "A thirsty crow, flying over a field in search of water, finally spotted a pitcher. He flew down eagerly to drink, but when he reached it, he found that it contained only a little water at the very bottom.\n\nThe crow tried to reach the water, but the neck of the pitcher was too narrow, and his beak was too short. He tried to tilt the pitcher, but it was too heavy for him to tip over.\n\nHe thought for a moment. Then, he looked around and saw some small pebbles scattered on the ground.\n\nOne by one, the crow picked up the pebbles in his beak and dropped them into the pitcher. With each pebble he dropped, the water rose a little higher.\n\nHe kept dropping pebbles until the water reached the top of the neck. Finally, the clever crow was able to quench his thirst.\n\nMoral: Little by little does the trick. Thoughtfulness and patience succeed where force fails."
    })
    stories.append({
        "id": "aesop-wind-and-sun",
        "title": "The Wind and the Sun",
        "author": "Aesop",
        "category": "mid",
        "content": "The Wind and the Sun had a dispute about which was the stronger of the two. While they were disputing, a traveler came along wrapped in a warm cloak.\n\nThey agreed that the one who should first succeed in making the traveler take off his cloak should be considered the stronger.\n\nThe Wind began first. He blew with all his might, a cold, howling blast. But the harder he blew, the closer the traveler wrapped his cloak around him, and the tighter he held it.\n\nThen the Sun took his turn. He shone out with all his warmth. The traveler felt the genial heat, and as he walked, he grew warmer and warmer. Soon, he began to unbutton his cloak, and at last, he threw it off altogether, and sat down in the shade of a nearby tree to rest.\n\nMoral: Gentle persuasion and warmth are often far more powerful than force and bluster."
    })

    try:
        index_html = fetch_with_curl("https://aesopfables.com/aesopsel.html")
        if index_html:
            links = re.findall(r'href=["\'](/cgi/aesop1\.cgi\?sel\&[^"\']+)["\']', index_html)
            links = list(set(links))
            print(f"Found {len(links)} Aesop Fables links in index.")
            
            scraped_count = 0
            for rel_link in links:
                if scraped_count >= 80:
                    break
                    
                if "CrowandthePitcher" in rel_link:
                    continue
                    
                try:
                    fable_url = "https://aesopfables.com" + rel_link
                    fable_html = fetch_with_curl(fable_url)
                    if not fable_html:
                        continue
                    
                    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', fable_html, re.DOTALL | re.IGNORECASE)
                    if pre_match:
                        content_raw = pre_match.group(1)
                        clean_text = clean_html(content_raw)
                        lines = [l.strip() for l in clean_text.split('\n') if l.strip()]
                        if len(lines) < 3:
                            continue
                            
                        title = lines[0]
                        story_lines = lines[1:]
                        story_text = "\n\n".join(story_lines)
                        
                        story_id = "aesop-scraped-" + title.lower().replace(" ", "-").replace("?", "").replace(",", "").replace("!", "")
                        story_id = re.sub(r'[^a-z0-9\-]', '', story_id)[:40]
                        
                        stories.append({
                            "id": story_id,
                            "title": title,
                            "author": "Aesop",
                            "category": "mid",
                            "content": story_text
                        })
                        scraped_count += 1
                        print(f"Scraped Aesop Fable {scraped_count}: {title}")
                except Exception as inner_e:
                    print(f"Error fetching Aesop Fable {rel_link}: {inner_e}")
                    
    except Exception as e:
        print(f"Error scraping Aesop: {e}")
        
    return stories

# ----------------- 3. SCRAPE MULLA NASRUDDIN -----------------
def scrape_nasruddin():
    print("\n--- SCRAPING MULLA NASRUDDIN STORIES ---")
    stories = []
    
    try:
        # Fetch Laura Gibbs' Nasruddin.txt database
        txt_content = fetch_with_curl("https://nasruddin.lauragibbs.net/Nasruddin.txt")
        if txt_content:
            story_blocks = re.split(r'\n(?=~\s*\d+\.\s*)', txt_content)
            print(f"Parsed {len(story_blocks)} potential blocks in Nasruddin.txt")
            
            scraped_count = 0
            for block in story_blocks:
                if not block.strip().startswith("~"):
                    continue
                    
                if scraped_count >= 150:
                    break
                    
                try:
                    title_match = re.search(r'^~\s*\d+\.\s*(.*?)\s*~', block)
                    if title_match:
                        title = title_match.group(1).strip()
                        content = block[title_match.end():].strip()
                        
                        if len(content) < 50:
                            continue
                            
                        story_id = f"nasruddin-tale-{scraped_count + 1}"
                        stories.append({
                            "id": story_id,
                            "title": title,
                            "author": "Mulla Nasruddin",
                            "category": "mid",
                            "content": content
                        })
                        scraped_count += 1
                except Exception as inner_e:
                    print(f"Error parsing Nasruddin block: {inner_e}")
                    
            print(f"Successfully compiled {scraped_count} Mulla Nasruddin stories.")
            
    except Exception as e:
        print(f"Error scraping Mulla Nasruddin: {e}")
        
    return stories

# ----------------- 4. COMPILATION OF ZEN STORIES FROM 2 SOURCES (Author: Zen) -----------------
def scrape_all_zen():
    print("\n--- COMPILING ZEN STORIES FROM ASHIDA KIM & SOTO ZEN ---")
    zen_stories = []
    
    # 4A. Static/Initial standard Zen stories
    zen_stories.append({
        "id": "zen-cup-of-tea",
        "title": "A Cup of Tea",
        "author": "Zen",
        "category": "flash",
        "content": "Nan-in, a Japanese master during the Meiji era, received a university professor who came to inquire about Zen.\n\nNan-in served tea. He poured his visitor's cup full, and then kept on pouring.\n\nThe professor watched the overflow until he no longer could restrain himself. \"It is overfull. No more will go in!\"\n\n\"Like this cup,\" Nan-in said, \"you are full of your own opinions and speculations. How can I show you Zen unless you first empty your cup?\"",
        "source": "Static"
    })
    zen_stories.append({
        "id": "zen-is-that-so",
        "title": "Is That So?",
        "author": "Zen",
        "category": "mid",
        "content": "The Zen master Hakuin was praised by his neighbors as a man living a pure life.\n\nA beautiful Japanese girl whose parents owned a food store lived near him. Suddenly, without any warning, her parents discovered she was with child. This made her parents very angry. She would not confess who the man was, but after much harassment she finally named Hakuin.\n\nIn great anger the parents went to the master. \"Is that so?\" was all he would say.\n\nAfter the child was born it was brought to Hakuin. By this time he had lost his reputation, which did not trouble him, but he took very good care of the child. He obtained milk from his neighbors and everything else the little one needed.\n\nA year later the girl-mother could stand it no longer. She told her parents the truth - that the real father of the child was a young man who worked in the fishmarket.\n\nThe mother and father of the girl at once went to Hakuin to ask his forgiveness, to apologize at length, and to get the child back.\n\nHakuin was willing. In yielding the child, all he said was: \"Is that so?\"",
        "source": "Static"
    })
    zen_stories.append({
        "id": "zen-muddy-road",
        "title": "The Muddy Road",
        "author": "Zen",
        "category": "mid",
        "content": "Tanzan and Ekido were once traveling together down a muddy road. A heavy rain was still falling.\n\nComing around a bend, they met a lovely girl in a silk kimono and sash, unable to cross the intersection because it was so muddy.\n\n\"Come on, girl,\" Tanzan said at once. Lifting her in his arms, he carried her over the mud.\n\nEkido did not speak again until that night when they reached a lodging temple. Then he no longer could restrain himself. \"We monks are not supposed to go near women,\" he told Tanzan, \"especially not young and lovely ones. It is dangerous. Why did you do that?\"\n\n\"I left the girl there by the road,\" Tanzan replied. \"Are you still carrying her?\"",
        "source": "Static"
    })

    # 4B. Scrape Ashida Kim
    try:
        index_html = fetch_with_curl("https://ashidakim.com/zenkoans/zenindex.html")
        if index_html:
            links = re.findall(r'href=["\'](?:https://ashidakim\.com/zenkoans/)?(\d+[^"\']+\.html)["\']', index_html)
            links = sorted(list(set(links)))
            print(f"Found {len(links)} Zen Koan links in Ashida Kim.")
            
            scraped_count = 0
            for rel_link in links:
                try:
                    koan_url = "https://ashidakim.com/zenkoans/" + rel_link
                    koan_html = fetch_with_curl(koan_url)
                    if not koan_html:
                        continue
                    
                    soup = BeautifulSoup(koan_html, "html.parser")
                    h1 = soup.find("h1")
                    main = soup.find("main")
                    
                    if h1 and main:
                        title_full = clean_html(str(h1))
                        title = re.sub(r'^\d+\.\s*', '', title_full).strip()
                        
                        breadcrumbs = main.find(class_="breadcrumbs")
                        if breadcrumbs:
                            breadcrumbs.decompose()
                            
                        story_text = clean_html(str(main))
                        lines = story_text.split('\n')
                        clean_lines = []
                        for line in lines:
                            if "Zen Koans Index" in line or "Site Home" in line or title in line:
                                continue
                            clean_lines.append(line)
                        story_text = "\n\n".join([l.strip() for l in clean_lines if l.strip()])
                        
                        if len(story_text) < 100:
                            continue
                            
                        story_id = "zen-ashida-" + title.lower().replace(" ", "-").replace("?", "").replace(",", "").replace("!", "")
                        story_id = re.sub(r'[^a-z0-9\-]', '', story_id)[:40]
                        
                        zen_stories.append({
                            "id": story_id,
                            "title": title,
                            "author": "Zen",
                            "category": "mid",
                            "content": story_text,
                            "source": "Ashida Kim"
                        })
                        scraped_count += 1
                except Exception as inner_e:
                    print(f"Error parsing Ashida Kim koan {rel_link}: {inner_e}")
            print(f"Successfully scraped {scraped_count} stories from Ashida Kim.")
    except Exception as e:
        print(f"Error scraping Ashida Kim: {e}")

    # 4C. Scrape Soto Zen
    try:
        print("Scraping Soto Zen stories...")
        soto_count = 0
        for i in range(1, 11):
            url = f"https://www.sotozen.com/eng/library/stories/vol{i:02d}.html"
            html_raw = fetch_with_curl(url)
            if not html_raw:
                continue
                
            soup = BeautifulSoup(html_raw, "html.parser")
            h2 = soup.find("h2", class_="h2_content")
            title = h2.get_text().strip() if h2 else f"Soto Zen Story {i}"
            title = re.sub(r'\s+', ' ', title).strip()
            
            stories_div = soup.find("div", class_="stories")
            if stories_div:
                p_tags = stories_div.find_all("p")
                paragraphs = []
                for p in p_tags:
                    text = p.get_text().strip()
                    text = re.sub(r'\s+', ' ', text).strip()
                    if text:
                        paragraphs.append(text)
                story_text = "\n\n".join(paragraphs)
                
                story_id = f"zen-soto-vol{i:02d}"
                zen_stories.append({
                    "id": story_id,
                    "title": title,
                    "author": "Zen",
                    "category": "deep",
                    "content": story_text,
                    "source": "Soto Zen"
                })
                soto_count += 1
                print(f"Scraped Soto Zen vol {i}: {title}")
        print(f"Successfully scraped {soto_count} stories from Soto Zen.")
    except Exception as e:
        print(f"Error scraping Soto Zen: {e}")
        
    return zen_stories

# ----------------- 5. SCRAPE SADHGURU'S STORIES (Zen & Buddha) (Author: Sadhguru) -----------------
def scrape_sadhguru_zen_articles():
    print("\nScraping Sadhguru Zen stories from topic page...")
    stories = []
    index_url = "https://isha.sadhguru.org/en/topic/zen-story"
    html_raw = fetch_with_curl(index_url)
    if not html_raw:
        return []
        
    links = re.findall(r'href=["\']([^"\']+)["\']', html_raw)
    urls = set()
    for href in links:
        if "wisdom/article/" in href:
            if "linkurl=" in href:
                parsed = urllib.parse.urlparse(href)
                query = urllib.parse.parse_qs(parsed.query)
                if "linkurl" in query:
                    u = query["linkurl"][0]
                    if "/wisdom/article/" in u:
                        urls.add(u)
            else:
                if href.startswith("/"):
                    urls.add("https://isha.sadhguru.org" + href)
                else:
                    urls.add(href)
                    
    raw_links = re.findall(r'linkurl=(https://isha\.sadhguru\.org/en/wisdom/article/[a-zA-Z0-9\-]+)', html_raw)
    for rl in raw_links:
        urls.add(rl)
        
    final_urls = sorted(list({u.split("?")[0].strip() for u in urls if "/wisdom/article/" in u and "11-intriguing-buddha-stories-by-sadhguru" not in u}))
    print(f"Found {len(final_urls)} Sadhguru Zen story links.")
    
    sadh_count = 0
    for idx, u in enumerate(final_urls):
        time.sleep(1.2)
        try:
            html_content = fetch_with_curl(u)
            if not html_content:
                continue
                
            soup = BeautifulSoup(html_content, "html.parser")
            h1 = soup.find("h1")
            title = h1.get_text().strip() if h1 else "Sadhguru Zen Story"
            title = re.sub(r'\s+', ' ', title).strip()
            title = title.replace("\u2014", " - ").replace("\u2013", " - ")
            title = re.sub(r'\s*-\s*a\s+zen\s+story.*', '', title, flags=re.IGNORECASE).strip()
            title = re.sub(r'\s*-\s*a\s+zen\s+parable.*', '', title, flags=re.IGNORECASE).strip()
            title = re.sub(r'\s*-\s*\s*A\s+Zen\s+Story.*', '', title, flags=re.IGNORECASE).strip()
            title = re.sub(r'\s*-\s*\s*A\s+Zen\s+Parable.*', '', title, flags=re.IGNORECASE).strip()
            title = re.sub(r'\s*\s*a\s+zen\s+story.*', '', title, flags=re.IGNORECASE).strip()
            title = re.sub(r'\s*\s*A\s+Zen\s+Story.*', '', title, flags=re.IGNORECASE).strip()
            
            body_el = soup.find(class_=lambda x: x and x.startswith("articlebody"))
            paragraphs = []
            if body_el:
                p_tags = body_el.find_all("p")
                for p in p_tags:
                    text = p.get_text().strip()
                    text = re.sub(r'\s+', ' ', text).strip()
                    if not text:
                        continue
                    if any(k in text.lower() for k in ["subscribe", "newsletter", "sign up", "join 1.2 million", "rights reserved", "support.ishafoundation.org"]):
                        continue
                    paragraphs.append(text)
                    
            story_text = "\n\n".join(paragraphs)
            if len(story_text) < 150:
                continue
                
            story_id = "sadhguru-scraped-zen-" + title.lower().replace(" ", "-").replace("?", "").replace(",", "").replace("!", "")
            story_id = re.sub(r'[^a-z0-9\-]', '', story_id)[:40]
            
            stories.append({
                "id": story_id,
                "title": title,
                "author": "Sadhguru", # Filed under Sadhguru
                "category": "mid",
                "content": story_text,
                "source": "Sadhguru Zen Article"
            })
            sadh_count += 1
            print(f"Scraped Sadhguru Zen story {sadh_count}/{len(final_urls)}: {title}")
        except Exception as inner_e:
            print(f"Error scraping Sadhguru article {u}: {inner_e}")
            
    return stories

def scrape_buddha_stories_by_sadhguru():
    print("\nScraping 11 Buddha stories by Sadhguru...")
    stories = []
    url = "https://isha.sadhguru.org/en/wisdom/article/11-intriguing-buddha-stories-by-sadhguru"
    html_raw = fetch_with_curl(url)
    if not html_raw:
        return []
        
    soup = BeautifulSoup(html_raw, "html.parser")
    body_el = soup.find(class_=lambda x: x and x.startswith("articlebody"))
    if not body_el:
        return []
        
    elements = body_el.find_all(["h2", "h3", "h4", "p"])
    current_story = None
    
    for el in elements:
        text = el.get_text().strip()
        if not text:
            continue
            
        m = re.match(r'^#(\d+)\.?\s*(.*)', text)
        if m:
            if current_story:
                stories.append(current_story)
            story_num = int(m.group(1))
            story_title = m.group(2).strip()
            story_title = story_title.replace("\u2019", "'").replace("\u201d", '"').replace("\u201c", '"')
            story_title = story_title.replace("\u2013", "-").replace("\u2014", "--")
            story_title = re.sub(r'\s*-\s*a\s+zen\s+story.*', '', story_title, flags=re.IGNORECASE).strip()
            
            current_story = {
                "num": story_num,
                "title": story_title,
                "paragraphs": []
            }
        else:
            if current_story:
                if any(k in text.lower() for k in ["subscribe", "newsletter", "sign up", "join 1.2 million", "rights reserved", "support.ishafoundation.org"]):
                    continue
                current_story["paragraphs"].append(text)
                
    if current_story:
        stories.append(current_story)
        
    final_stories = []
    for s in stories:
        content_text = "\n\n".join(s["paragraphs"])
        if len(content_text) < 150:
            continue
            
        story_id = f"sadhguru-scraped-buddha-{s['num']}"
        final_stories.append({
            "id": story_id,
            "title": s["title"],
            "author": "Sadhguru", # Filed under Sadhguru
            "category": "mid",
            "content": content_text,
            "source": "Sadhguru Buddha Stories"
        })
        print(f"Scraped Sadhguru Buddha story #{s['num']}: {s['title']}")
        
    return final_stories

# ----------------- Curated Static additions (JK & Sadhguru) -----------------
def get_jk_stories():
    return [
        {
            "id": "jk-devil-and-friend",
            "title": "The Devil and His Friend",
            "author": "J. Krishnamurti",
            "category": "mid",
            "content": "Jiddu Krishnamurti often told this story to illustrate how truth gets organized and lost:\n\nOne day, the devil and a friend were walking down the street. A short distance ahead, they saw a man bend down, pick something up from the ground, look at it, and put it in his pocket.\n\nThe friend turned to the devil and asked, \"What did that man just find?\"\n\n\"He found a piece of Truth,\" the devil replied.\n\nThe friend was shocked. \"Doesn't that worry you? If he has found the truth, your business is finished!\"\n\nThe devil smiled and shook his head. \"Not at all. I am going to let him organize it.\""
        },
        {
            "id": "jk-the-cage",
            "title": "The Bird in the Cage",
            "author": "J. Krishnamurti",
            "category": "mid",
            "content": "There is a story of a bird that lived in a golden cage, beautifully adorned with jewels. The bird was fed the most delicious seeds and given fresh water daily. It sang beautiful songs, and people came from all over to listen.\n\nOne day, a wild bird flew from a nearby forest and landed on the windowsill outside the cage. The wild bird looked at the caged bird and said, \"Why do you sing? You are imprisoned behind these gold bars. You cannot fly in the open sky, you cannot feel the wind beneath your wings, and you do not know what it means to be truly alive.\"\n\nThe caged bird replied, \"But look at my cage! It is made of gold, it is safe, I have no predators, and I am fed every day. Why would I want to leave?\"\n\nThe wild bird shook its head and flew away. \n\nKrishnamurti uses this story to show that our minds are like that caged bird. We build cages of comfort, beliefs, dogmas, and security. We think we are happy because our cages are decorated, but we are prisoners of our own conditioning, terrified of the vast, open sky of freedom."
        }
    ]

def get_sadhguru_stories():
    return [
        {
            "id": "sadhguru-bull-and-pheasant",
            "title": "The Bull and the Pheasant",
            "author": "Sadhguru",
            "category": "mid",
            "content": "A bull and a pheasant were grazing in a field. The pheasant looked up at a tall tree and said, \"Alas, there was a time I could fly to the topmost branch, but now I don't have the strength even for the first branch.\"\n\nThe bull casually replied, \"Just eat a little bit of my dung every day; you will see that within a fortnight, you will reach the top.\"\n\nThe pheasant was skeptical, but he decided to try it. He pecked at a small piece of dung. To his surprise, he found it gave him enough energy to fly to the first branch of the tree the very first day.\n\nThe next day, he ate a bit more and flew to the second branch. Within two weeks, he was proudly sitting on the very top of the tree, enjoying the view.\n\nA passing farmer noticed a fat, slow pheasant sitting on the highest branch of his tree. He quietly raised his shotgun and shot the pheasant down.\n\nMoral: Deceptive shortcuts might get you to the top, but they will never keep you there. Real growth requires real work."
        },
        {
            "id": "sadhguru-the-fruit-of-silence",
            "title": "The Fruit of Silence",
            "author": "Sadhguru",
            "category": "mid",
            "content": "A disciple went to a Zen master and said, \"Master, I want to experience absolute silence. Please teach me how to quiet my mind.\"\n\nThe master looked at him and said, \"For the next seven days, you shall not speak a single word. Whatever happens, maintain complete silence.\"\n\nThe disciple was thrilled. On the first day, he sat under a tree and watched his breath. By evening, another monk walked past and accidentally dropped a bucket of water near him. The disciple yelled, \"Hey! Watch what you are doing!\"\n\nImmediately, he realized his mistake. He went to the master and apologized, saying, \"I failed on the very first day. I spoke.\"\n\nThe master replied, \"Why are you worried about the monk's water? You did not speak because of the water. You spoke because your mind was already filled with chattering. Silence is not about stopping your tongue; it is about emptying the mind. When there is no chatter inside, even if you shout, you remain in silence.\""
        }
    ]

def enrich_story(s):
    s["category"] = assign_category_by_length(s["content"])
    s["wordCount"] = len(s["content"].split())
    s["readTime"] = max(1, (s["wordCount"] + 199) // 200)
    return s

# ----------------- MAIN RUNNER -----------------
def main():
    print("Starting crawl and compilation script...")
    
    # 1. Scrape Osho Stories
    osho_stories = [enrich_story(s) for s in scrape_osho()]
    with open(os.path.join(STORIES_DIR, "osho.js"), "w", encoding="utf-8") as f:
        f.write(f"const STORIES_OSHO = {json.dumps(osho_stories, indent=2)};")
    print(f"Saved {len(osho_stories)} Osho stories.")
    
    # 2. Scrape Zen Stories & Deduplicate (Only Ashida Kim and Soto Zen, Author: Zen)
    all_raw_zen = scrape_all_zen()
    zen_stories = [enrich_story(s) for s in deduplicate_stories(all_raw_zen, "Zen")]
    with open(os.path.join(STORIES_DIR, "zen.js"), "w", encoding="utf-8") as f:
        f.write(f"const STORIES_ZEN = {json.dumps(zen_stories, indent=2)};")
    print(f"Saved {len(zen_stories)} unique Zen stories.")
    
    # 3. Scrape Sadhguru Stories (Static + Scraped Zen & Buddha stories, Author: Sadhguru)
    static_sadhguru = get_sadhguru_stories()
    scraped_sadhguru_zen = scrape_sadhguru_zen_articles()
    scraped_sadhguru_buddha = scrape_buddha_stories_by_sadhguru()
    
    all_raw_sadhguru = static_sadhguru + scraped_sadhguru_zen + scraped_sadhguru_buddha
    sadhguru_stories = [enrich_story(s) for s in deduplicate_stories(all_raw_sadhguru, "Sadhguru")]
    with open(os.path.join(STORIES_DIR, "sadhguru.js"), "w", encoding="utf-8") as f:
        f.write(f"const STORIES_SADHGURU = {json.dumps(sadhguru_stories, indent=2)};")
    print(f"Saved {len(sadhguru_stories)} unique Sadhguru stories.")
    
    # 4. Scrape Aesop Fables
    aesop_stories = [enrich_story(s) for s in scrape_aesop()]
    with open(os.path.join(STORIES_DIR, "aesop.js"), "w", encoding="utf-8") as f:
        f.write(f"const STORIES_AESOP = {json.dumps(aesop_stories, indent=2)};")
    print(f"Saved {len(aesop_stories)} Aesop fables.")
    
    # 5. Scrape Mulla Nasruddin
    nasruddin_stories = [enrich_story(s) for s in scrape_nasruddin()]
    with open(os.path.join(STORIES_DIR, "nasruddin.js"), "w", encoding="utf-8") as f:
        f.write(f"const STORIES_NASRUDDIN = {json.dumps(nasruddin_stories, indent=2)};")
    print(f"Saved {len(nasruddin_stories)} Mulla Nasruddin stories.")
    
    # 6. Get J. Krishnamurti Stories
    jk_stories = [enrich_story(s) for s in get_jk_stories()]
    with open(os.path.join(STORIES_DIR, "jk.js"), "w", encoding="utf-8") as f:
        f.write(f"const STORIES_JK = {json.dumps(jk_stories, indent=2)};")
    print(f"Saved {len(jk_stories)} J. Krishnamurti stories.")

    print("\n--- ALL STORIES COMPLETED, DEDUPLICATED AND CATEGORIZED BY AUTHOR AND READ-TIME ---")

if __name__ == "__main__":
    main()
