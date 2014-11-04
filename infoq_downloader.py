#!/usr/bin/env python

from __future__ import division, print_function
import os
from pathlib import Path
import sys
import re
import argparse
import requests
import cssselect
import lxml.html
import unicodedata

if sys.version_info.major == 3:
    text_type = str
else:
    text_type = unicode


# Some settings
download_directory = Path('downloads')
cleanup_elements = [
    '#footer', '#header', '#topInfo', '.share_this', '.random_links',
    '.vendor_vs_popular', '.bottomContent', '#id_300x250_banner_top',
    '.presentation_type', '#conference', '#imgPreload', '#text_height_fix_box',
    '.download_presentation', '.recorded', 'script[async]',
    'script[src*=addthis]'
]

# Set argparse to parse the paramaters
parser = argparse.ArgumentParser(description='Download InfoQ presentations.')
parser.add_argument('url', metavar='URL', type=str,
                    help='URL of the presentation to download')

# Parse the arguments passed to the script
args = parser.parse_args()
url = args.url

# Tell infoq that I'm an iPad, so it gives me simpler HTML to parse & mp4 file
# qto download
user_agent = (
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) "
    "AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b "
    "Safari/531.21.10')"
)

# Start downloading
print('Downloading HTML file')

content = requests.get(url, headers={'User-Agent': user_agent}).text
html_doc = lxml.html.fromstring(content)
title = html_doc.find(".//title").text
if not isinstance(title, text_type):
    title = title.decode() # lxml python2 fix
video_url = html_doc.cssselect('video > source')[0].attrib['src']
video_file = os.path.split(video_url)[1]
html_doc.cssselect('video > source')[0].attrib['src'] = video_file

# Clean the page
for elt in html_doc.cssselect(', '.join(e for e in cleanup_elements)):
    elt.getparent().remove(elt)
html_doc.cssselect('#wrapper')[0].attrib['style'] = 'background: none'
content = lxml.html.tostring(html_doc).decode('utf-8')

# Make slides links point to local copies
slides_re = re.compile(r"'(/resource/presentations/[^']*?/en/slides/[^']*?)'")
slides = slides_re.findall(content)

# Create a directory for the downloaded presentation if it doesn't exist

def sanitize_path(name):
    sanitized = unicodedata.normalize('NFKD', name)
    if sys.platform == 'win32':
        sanitized = u''.join(c for c in sanitized if ord(c) > 31 and c not in u'<>:"/\|?*')
    return sanitized

presentation_directory = download_directory / sanitize_path(title)
slides_dir = presentation_directory / 'slides'

# Create a slides folder inside the presentation folder
if not slides_dir.exists():
    slides_dir.mkdir(parents=True)


#Write content
content = re.sub(r"/resource/presentations/[^']*?/en/", '', content)
with (presentation_directory / 'index.html').open('w') as f:
    f.write(content)

# Download slides
for i, slide in enumerate(slides):
    full_path = slides_dir / os.path.split(slide)[1]
    if full_path.exists():
        continue
    print('\rDownloading slide {0} of {1}'.format(i+1, len(slides)), end='')
    sys.stdout.flush()  # Hack for Python 2
    url = 'http://www.infoq.com{0}'.format(slide)

    with full_path.open('wb') as f:
        f.write(requests.get(url).content)

print()

# If the video file is already downloaded successfully, don't do anything else
video_path = presentation_directory / video_file
if video_path.exists():
    print('Video file already exists')
    sys.exit()

# Download the video file. stream=True here is important to allow me to iterate
# over content
downloaded_file = presentation_directory / '{}.part'.format(video_file)

if downloaded_file.exists():
    bytes_downloaded = downloaded_file.stat().st_size
else:
    bytes_downloaded = 0

r = requests.get(video_url, stream=True,
                 headers={'Range': 'bytes={0}-'.format(bytes_downloaded)})
content_length = int(r.headers['content-length']) + bytes_downloaded

with downloaded_file.open('ab') as f:
    for chunk in r.iter_content(10 * 1024):
        f.write(chunk)
        f.flush()
        # \r used to return the cursor to beginning of line, so I can write
        # progress on a single line.
        # The comma at the end of line is important, to stop the 'print' command
        # from printing an additional new line
        percent = f.tell() / content_length * 100
        print('\rDownloading video {0:.2f}%'.format(percent), end='')
        sys.stdout.flush()  # Hack for Python 2

downloaded_file.rename(video_path)
