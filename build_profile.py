import feedparser
import functools
import re
import pathlib
import sys

root = pathlib.Path(__file__).parent.resolve()


def fetch_rss_feed(url, num_entries=5):
    feed = feedparser.parse(url)
    entries = feed.entries if num_entries == 0 else feed.entries[:num_entries]

    return [
        {
            'title': entry['title'],
            'link': entry['link'],
            'published': entry.get('published', ''),
            'status': _entry_status(entry),
        }
        for entry in entries
    ]


WITHDRAWN_RE = re.compile(r'\bwithdrawn\b|\bwithdrawal\b', re.IGNORECASE)


def _is_withdrawn(text):
    return bool(WITHDRAWN_RE.search(text or ''))


def _arxiv_id(link):
    m = re.search(r'arxiv\.org/abs/([^?#\s]+?)(?:v\d+)?$', link or '')
    return m.group(1) if m else None


def _withdrawn_via_api(link):
    # The RSS feed omits the comment field, where withdrawals are often noted.
    arxiv_id = _arxiv_id(link)
    if not arxiv_id:
        return False
    try:
        api = feedparser.parse(
            'https://export.arxiv.org/api/query?id_list={}'.format(arxiv_id)
        )
        return any(
            _is_withdrawn(
                ' '.join(
                    [
                        e.get('title', ''),
                        e.get('summary', ''),
                        e.get('arxiv_comment', ''),
                    ]
                )
            )
            for e in api.entries
        )
    except Exception:
        return False


def _entry_status(entry):
    status = entry.get('arxiv_announce_type', '')
    # Withdrawn papers are announced as replacements.
    text = ' '.join([entry.get('summary', ''), entry.get('title', '')])
    if _is_withdrawn(text):
        return 'withdrawn'
    if status.startswith('replace') and _withdrawn_via_api(entry.get('link')):
        return 'withdrawn'
    return status


STATUS_BADGES = {
    'new': ('new', '2ea44f'),
    'cross': ('cross--list', '0969da'),
    'replace': ('update', 'bf8700'),
    'replace-cross': ('update', 'bf8700'),
    'retract': ('retract', 'cf222e'),
    'withdrawn': ('withdrawn', 'cf222e'),
}


def status_badge(status):
    label, color = STATUS_BADGES.get(
        (status or '').strip().lower(), ((status or '').strip(), '6e7781')
    )
    if not label:
        return ''
    return '<img alt="{0}" src="https://img.shields.io/badge/-{0}-{1}?style=flat-square"> '.format(
        label, color
    )


@functools.lru_cache(maxsize=None)
def _chunk_pattern(marker):
    return re.compile(
        r'<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->'.format(marker, marker),
        re.DOTALL,
    )


def replace_chunk(content, marker, chunk, inline=False):
    r = _chunk_pattern(marker)
    if not inline:
        chunk = '\n{}\n'.format(chunk)
    chunk = '<!-- {} starts -->{}<!-- {} ends -->'.format(marker, chunk, marker)
    chunk = chunk.replace('\\', '')

    return r.sub(chunk, content)


if __name__ == '__main__':
    readme = root / 'README.md'
    readme_contents = readme.read_text()

    try:
        entries = fetch_rss_feed('https://api.quantamagazine.org/feed/')
        print('Recent Posts on Quanta-Magazine\n')
        entries_md = '\n'.join(
            '* <a href="{link}">{title}</a> - {published}'.format(**entry)
            for entry in entries
        )
        readme_contents = replace_chunk(readme_contents, 'quanta', entries_md)
    except Exception as e:
        print('Error fetching Quanta feed: {}'.format(e), file=sys.stderr)

    try:
        entries = fetch_rss_feed('http://export.arxiv.org/rss/math.NA', 0)
        print('Recent Posts on Arxiv Math.NA\n')
        entries_md = '\n'.join(
            (
                '* {badge}<a href="{link}">{title}</a> - {published}'
                if entry['published']
                else '* {badge}<a href="{link}">{title}</a>'
            ).format(badge=status_badge(entry['status']), **entry)
            for entry in entries
        )
        readme_contents = replace_chunk(readme_contents, 'arxiv-math-na', entries_md)
    except Exception as e:
        print('Error fetching arXiv feed: {}'.format(e), file=sys.stderr)

    readme.write_text(readme_contents)
    print('Done!')
