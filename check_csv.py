with open('data/google_ads.csv', encoding='utf-8-sig') as f:
    for i, line in enumerate(f):
        print(i, line[:80])
        if i > 10:
            break