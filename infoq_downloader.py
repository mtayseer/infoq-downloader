# TODO: To complete download of the file, use HTTP header 'Range': 'bytes=20-'
from __future__ import division
import os
import sys
import re
import argparse
import requests
import lxml.html


# Set argparse to parse the paramaters
parser = argparse.ArgumentParser(description='Download InfoQ presentations.')
parser.add_argument('url', metavar='URL', type=str, help='URL of the presentation to download')

# read the paramaters
args = parser.parse_args()

# Set the url
url = args.url

# Tell infoq that I'm an iPad, so it gives me simpler HTML to parse & mp4 file to download
user_agent = "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 " \
             "(KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10')"

print 'Downloading HTML file'
content = requests.get(url, headers={'User-Agent': user_agent}).content
html_doc = lxml.html.fromstring(content)
title = html_doc.find(".//title").text
video_url = html_doc.cssselect('video > source')[0].attrib['src']
video_file = os.path.split(video_url)[1]
html_doc.cssselect('video > source')[0].attrib['src'] = video_file

# Clean the page
for elt in html_doc.cssselect('#footer, #header, #topInfo, .share_this, .random_links,' +
                              ' .vendor_vs_popular, .bottomContent, #id_300x250_banner_top,' +
                              ' .presentation_type, #conference, #imgPreload, #text_height_fix_box, ' +
                              '.download_presentation, .recorded, script[async]'):
    elt.getparent().remove(elt)
html_doc.cssselect('#wrapper')[0].attrib['style'] = 'background: none'
content = lxml.html.tostring(html_doc)

# Make slides links point to local copies
slides_re = re.compile(r"'(/resource/presentations/[^']*?/en/slides/[^']*?)'")
slides = slides_re.findall(content)

# Create a directory for the downloaded presentation
download_directory = 'downloads'

# If the downloads folder does not exist, create it
if not os.path.exists('{}'.format(download_directory)):
    os.makedirs('{}'.format(download_directory))

# Create a folder with the name of the presentation
if not os.path.exists('{}/{}'.format(download_directory, title)):
    os.makedirs('{}/{}'.format(download_directory, title))

# Create a slides folder inside the presentation folder
if not os.path.exists('{}/{}/slides'.format(download_directory, title)):
    os.makedirs('{}/{}/slides'.format(download_directory, title))

content = re.sub(r"/resource/presentations/[^']*?/en/", '', content)
with open('{}/{}/index.html'.format(download_directory, title), 'w') as f:
    f.write(content)
    f.flush()

for i, slide in enumerate(slides):
    filename = os.path.split(slide)[1]
    if os.path.exists('{}/{}'.format(download_directory, title) + '/slides/{0}'.format(filename)):
        continue
    print '\rDownloading slide {0} of {1}'.format(i, len(slides)),
    url = 'http://www.infoq.com{0}'.format(slide)
    open('{}/{}'.format(download_directory, title) + '/slides/{0}'.format(filename), 'wb').write(requests.get(url).content)

print

# If the video file is already downloaded successfully, don't do anything else
if os.path.exists(video_file):
    sys.exit()

# Download the video file. stream=True here is important to allow me to iterate over content
downloaded_file = '{}/{}/{}.part'.format(download_directory, title, video_file)
if os.path.exists(downloaded_file):
    bytes_downloaded = os.stat(downloaded_file).st_size
else:
    bytes_downloaded = 0

r = requests.get(video_url, stream=True, headers={'Range': 'bytes={0}-'.format(bytes_downloaded)})
content_length = int(r.headers['content-length']) + bytes_downloaded

with open(downloaded_file, 'ab') as f:
    for chunk in r.iter_content(10 * 1024):
        f.write(chunk)
        f.flush()
        # \r used to return the cursor to beginning of line, so I can write progress on a single line.
        # The comma at the end of line is important, to stop the 'print' command from printing an additional new line
        print '\rDownloading video {0}%'.format(round(f.tell() / content_length, 2) * 100),

os.rename(downloaded_file, video_file)
