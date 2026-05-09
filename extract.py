#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime

def main():
    payload_file = 'payload.json'
    if not os.path.exists(payload_file):
        print("❌ No payload.json found")
        sys.exit(1)
    
    with open(payload_file, 'r') as f:
        payload = json.load(f)
    
    # Try multiple locations where the URL could be
    url = None
    
    # Browser bookmarklet sends: client_payload.url
    if 'client_payload' in payload and 'url' in payload['client_payload']:
        url = payload['client_payload']['url']
    
    # curl with --data sends directly
    elif 'url' in payload:
        url = payload['url']
    
    # Some implementations use action or inputs
    elif 'inputs' in payload and 'url' in payload['inputs']:
        url = payload['inputs']['url']
    
    # Fallback: check the event action
    elif 'action' in payload and payload['action'] == 'new-url':
        # URL might be in the payload body
        pass
    
    if not url:
        print("❌ No URL found in payload")
        print(f"📋 Payload keys: {list(payload.keys())}")
        if 'client_payload' in payload:
            print(f"   client_payload keys: {list(payload['client_payload'].keys())}")
        sys.exit(1)
    
    print(f"✅ Found URL: {url}")
    
    # Load or create metadata.json
    metadata_file = 'metadata.json'
    existing = []
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing] if existing else []
    
    # Check for duplicate
    urls_existing = [a.get('url') for a in existing if isinstance(a, dict)]
    if url not in urls_existing:
        existing.append({
            'url': url,
            'title': url,
            'saved_at': datetime.now().isoformat()
        })
        print(f"✅ Added: {url[:80]}...")
    else:
        print(f"⏭️ Duplicate, skipping: {url[:80]}...")
    
    with open(metadata_file, 'w') as f:
        json.dump(existing, f, indent=2)
    
    print(f"📊 Total saved: {len(existing)}")

if __name__ == "__main__":
    main()
