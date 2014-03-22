from __future__ import division
import os
import sys
import re
import argparse
import requests
import cssselect
import lxml.html


# Some settings
download_directory = 'downloads'
cleanup_elements = ['#footer', '#header', '#topInfo', '.share_this', '.random_links', '.vendor_vs_popular',
                    '.bottomContent', '#id_300x250_banner_top', '.presentation_type', '#conference', '#imgPreload',
                    '#text_height_fix_box', '.download_presentation', '.recorded', 'script[async]', 
                    'script[src*=addthis]']

# Set argparse to parse the paramaters
parser = argparse.ArgumentParser(description='Download InfoQ presentations.')
parser.add_argument('url', metavar='URL', type=str, help='URL of the presentation to download')

# Parse the arguments passed to the script
args = parser.parse_args()
url = args.url

# Tell infoq that I'm an iPad, so it gives me simpler HTML to parse & mp4 file to download
user_agent = "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 " \
             "(KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10')"

# Start downloading
print 'Downloading HTML file'

content = requests.get(url, headers={'User-Agent': user_agent}).content
html_doc = lxml.html.fromstring(content)
title = html_doc.find(".//title").text
video_url = html_doc.cssselect('video > source')[0].attrib['src']
video_file = os.path.split(video_url)[1]
html_doc.cssselect('video > source')[0].attrib['src'] = video_file

# Clean the page
for elt in html_doc.cssselect(', '.join(e for e in cleanup_elements)):
    elt.getparent().remove(elt)
html_doc.cssselect('#wrapper')[0].attrib['style'] = 'background: none'
content = lxml.html.tostring(html_doc)

# Make slides links point to local copies
slides_re = re.compile(r"'(/resource/presentations/[^']*?/en/slides/[^']*?)'")
slides = slides_re.findall(content)

# Create a directory for the downloaded presentation if it doesn't exist
if not os.path.exists(download_directory):
    os.makedirs(download_directory)

# presentation folder path
presentation_directory = os.path.join(download_directory, title)
# Create a folder with the name of the presentation
if not os.path.exists(presentation_directory):
    os.makedirs(presentation_directory)

# Create a slides folder inside the presentation folder
if not os.path.exists('{}/slides'.format(presentation_directory)):
    os.makedirs('{}/slides'.format(presentation_directory))

#Write content
content = re.sub(r"/resource/presentations/[^']*?/en/", '', content)
with open('{}/index.html'.format(presentation_directory), 'w') as f:
    f.write(content)
    f.flush()

# Download slides
for i, slide in enumerate(slides):
    filename = os.path.split(slide)[1]
    if os.path.exists(os.path.join(presentation_directory, 'slides', '{0}'.format(filename))):
        continue
    print '\rDownloading slide {0} of {1}'.format(i+1, len(slides)),
    url = 'http://www.infoq.com{0}'.format(slide)
    with open(os.path.join(presentation_directory, 'slides', '{0}'.format(filename)), 'wb') as f:
        f.write(requests.get(url).content)

print

# If the video file is already downloaded successfully, don't do anything else
if os.path.exists(video_file):
    print 'Video file already exists'
    sys.exit()

# Download the video file. stream=True here is important to allow me to iterate over content
downloaded_file = os.path.join(presentation_directory, '{}.part'.format(video_file))

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

final_video_name = os.path.join(presentation_directory, video_file)
os.rename(downloaded_file, final_video_name)
