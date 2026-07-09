import requests
import random
from atproto import Client
from datetime import datetime
import os

# --- Config (pulled from GitHub Secrets as env vars) ---
BSKY_HANDLE = os.environ['BSKY_IDENTIFIER']
BSKY_PASSWORD = os.environ['BSKY_PASSWORD']

def get_random_reptile():
    """Fetch a random reptile observation with a photo from iNaturalist."""
    params = {
        'taxon_name': 'Reptilia',
        'has[]': 'photos',
        'quality_grade': 'research',
        'per_page': 30,
        'page': random.randint(1, 500),
        'license': 'cc-by,cc-by-nc',
    }
    r = requests.get('https://api.inaturalist.org/v1/observations', params=params)
    r.raise_for_status()
    results = r.json()['results']

    # Filter to ones that actually have photos
    with_photos = [o for o in results if o.get('photos')]

    # If that page was empty, fall back to page 1
    if not with_photos:
        params['page'] = 1
        r = requests.get('https://api.inaturalist.org/v1/observations', params=params)
        r.raise_for_status()
        results = r.json()['results']
        with_photos = [o for o in results if o.get('photos')]

    if not with_photos:
        raise ValueError("No observations with photos found")

    obs = random.choice(with_photos)
    photo = obs['photos'][0]
    img_url = photo['url'].replace('square', 'medium')

    name = obs['taxon']['name'] if obs.get('taxon') else 'Unknown reptile'
    common = obs['taxon'].get('preferred_common_name', '').title() if obs.get('taxon') else ''
    place = obs.get('place_guess', '')
    observer = obs['user']['login']

    caption_parts = []
    if common:
        caption_parts.append(f"🦎 {common} ({name})")
    else:
        caption_parts.append(f"🦎 {name}")
    if place:
        caption_parts.append(f"📍 {place}")
    caption_parts.append(f"📸 {observer} on iNaturalist")
    caption_parts.append(f"#reptiles #herpetology #iNaturalist")

    caption = '\n'.join(caption_parts)
    if len(caption) > 295:
        caption = caption[:292] + '...'

    return img_url, caption, name, common

def post_to_bluesky(img_url, caption, alt_text):
    img_data = requests.get(img_url).content

    client = Client()
    client.login(BSKY_HANDLE, BSKY_PASSWORD)
    client.send_image(
        text=caption,
        image=img_data,
        image_alt=alt_text
    )
    print(f"Posted: {caption[:60]}...")

if __name__ == '__main__':
    img_url, caption, name, common = get_random_reptile()
    alt_text = f"Photo of a {common or name}"
    post_to_bluesky(img_url, caption, alt_text)
