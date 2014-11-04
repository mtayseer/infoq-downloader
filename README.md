# InfoQ downloader

[InfoQ](http://www.infoq.com/) is a great resource for many useful sessions. The way they view presentations sync'ed with slides is cool. Unfortunately, I have a slow internet connection which makes my viewing experience sucks. To solve this, I made this scripts which downloads their page, video & slides.

## Installation
On Windows, just download [this file](dist/infoq_downloader.exe?raw=true)

On Linux, ensure you have the development headers neeeded by lxml (`sudo apt-get install libxml2-dev libxslt1-dev` on Ubuntu) and run the following:

```sh
git clone https://github.com/mtayseer/infoq-downloader.git
cd infoq-downloader
pip install -r requirements.txt
```

## Usage
`python infoq_downloader.py http://www.infoq.com/presentations/github-evolution`

On Windows
`infoq_downloader.exe http://www.infoq.com/presentations/github-evolution`

## Features
1. Console app
2. Supports download resuming of slides & videos
3. The generated HTML is clean

## License
MIT. See [LICENSE](LICENSE)