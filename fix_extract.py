import json, pathlib, sys, time
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from llm import ask_llm

cache = pathlib.Path('scraper/cache')

def clean(text):
    return (text
        .replace('â‚¹', 'Rs')
        .replace('âš¡', '')
        .replace('â˜…', '')
        .replace('Ã—', '')
        .replace('â€™', "'")
        .replace('â€œ', '"')
        .replace('â€', '"')
    )

def parse_json_safely(text):
    if not text or not text.strip():
        return None
    try:
        start = text.index('[')
        end = text.rindex(']') + 1
        return json.loads(text[start:end])
    except Exception:
        pass
    try:
        start = text.index('[')
        partial = text[start:].rstrip().rstrip(',')
        if not partial.endswith('}'):
            partial += '"}'
        if not partial.endswith(']'):
            partial += ']'
        return json.loads(partial)
    except Exception:
        pass
    return None

all_records = []
brands_done = []

for data_file in sorted(cache.glob('*_data.json')):
    if data_file.name == 'all_brands.json':
        continue
    try:
        existing = json.loads(data_file.read_text())
        if len(existing) > 0:
            brand = data_file.stem.replace('_data', '').replace('_', ' ').title()
            brands_done.append(data_file.stem)
            all_records.extend(existing)
            print(f'Skipping {brand} - already has {len(existing)} records')
    except Exception:
        pass

for raw_file in sorted(cache.glob('*_raw.txt')):
    brand_key = raw_file.stem.replace('_raw', '')
    data_key = brand_key + '_data'

    if data_key in brands_done:
        continue

    brand = brand_key.replace('_', ' ').title()
    data_file = cache / (brand_key + '_data.json')

    print(f'Extracting: {brand}...')
    raw = clean(raw_file.read_text(encoding='utf-8', errors='ignore'))

    if not raw.strip():
        print(f'  skipping - empty')
        continue

    prompt = f"""You are a market research analyst. Extract ALL freebies and free gift offers from this Indian skincare brand website text.

Brand: {brand}

Look for:
- FREE [product] above Rs[amount]
- Free gift on orders above Rs X
- Buy X get Y free
- Free sample or trial product

Return ONLY a JSON array. Each item must have these exact keys:
  "brand": "{brand}",
  "freebie": "name of free item",
  "condition": "order condition or null",
  "category": "skincare-trial or accessory or bundle or discount or other",
  "est_cost": null,
  "perceived_value": 70,
  "novelty": 50,
  "source_url": null

If nothing found return [].
No markdown. No explanation. Start your response with [ and end with ].

TEXT:
{raw[:3000]}"""

    time.sleep(4)

    result = ask_llm(prompt, system='Output valid JSON arrays only. Start with [ end with ].', temperature=0.1)
    records = parse_json_safely(result)

    if records is not None:
        print(f'  found {len(records)} records')
        data_file.write_text(json.dumps(records, indent=2), encoding='utf-8')
        all_records.extend(records)
    else:
        print(f'  could not parse response')
        if result:
            print(f'  response preview: {result[:200]}')

combined = cache / 'all_brands.json'
combined.write_text(json.dumps(all_records, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'\nDone. {len(all_records)} total records saved to scraper/cache/all_brands.json')