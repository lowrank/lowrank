import feedparser 
import re
import pathlib

root = pathlib.Path(__file__).parent.resolve()   

def fetch_rss_feed(url, num_entries=5):
    if num_entries == 0:
        entries = feedparser.parse(url).entries
    else:
        entries = feedparser.parse(url).entries[:num_entries]

    return [
        {
            'title': entry['title'],
            'link': entry['link'],
            'published': entry['published'] if 'published' in entry else '', 
        }
        for entry in entries
    ]

def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r'<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->'.format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = '\n{}\n'.format(chunk)
    chunk = '<!-- {} starts -->{}<!-- {} ends -->'.format(marker, chunk, marker)
    chunk = chunk.replace('\\','')

    return r.sub(chunk, content)

if __name__ == '__main__':
    readme = root / 'README.md'
    readme_contents = readme.open().read()
    entries = fetch_rss_feed('https://api.quantamagazine.org/feed/')

    print('Recent Posts on Quanta-Magazine\n')
    entries_md = '\n'.join(
        ['* <a href="{link}">{title}</a> - {published}'.format(**entry) for entry in entries]
    )

    rewritten = replace_chunk(readme_contents, 'quanta', entries_md)

    readme.open('w').write(rewritten)


    readme_contents = readme.open().read()
    entries = fetch_rss_feed('http://export.arxiv.org/rss/math.NA', 0)
    
    print('Recent Posts on Arxiv Math.NA\n')

    entries_md = '\n'.join(
        [('* <a href="{link}">{title}</a> - {published}' if len(entry['published'])>0 else '* <a href="{link}">{title}</a>').format(**entry) for entry in entries]
    )

    # print(entries_md)
    rewritten = replace_chunk(readme_contents, 'arxiv-math-na', entries_md)
    readme.open('w').write(rewritten)

    print('Done!')