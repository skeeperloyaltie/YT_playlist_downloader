from distutils.core import setup
setup(
    name='playlistDownloader',
    version='0.0.1',
    author='Skeeper Loyaltie',
    author_email='skeeperloyaltie@pm.me',
    url='skeeperloyaltie@pm.me',
    license='LICENSE',
    packages=['playlistDownloader'],
    description='Youtube Playlist Downloader',
    install_requires=[
    'yt_dlp',
    'pyfiglet'
    ]
)
