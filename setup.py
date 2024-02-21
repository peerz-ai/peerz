from distutils.core import setup
setup(
  name = 'peerz',
  packages = ['peerz'],
  version = '0.1.1',
  description = 'peerz',
  author = 'peerz',
  author_email = 'peerz',
  url = 'https://github.com/peerz-ai/peerz-ai',
  classifiers = [],
  entry_points={'console_scripts': [
    'peerz=peerz.cli.run:main',
  ]}
)
