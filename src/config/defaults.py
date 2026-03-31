"""
Default configuration values for PanDoG
"""

DEFAULT_CONFIG = {
    'General': {
        'language': 'en',
        'theme': 'system',
    },
    'Converter': {
        'pandoc_path': 'pandoc',
        'pandoc_options': '',
        'output_dir': '',
        'output_same_dir': 'True',
        'default_input_format': '',
        'default_output_format': 'html',
    },
    'UI': {
        'window_width': 1200,
        'window_height': 800,
        'window_x': '',
        'window_y': '',
    },
    'Recent': {
        'max_recent_items': 10,
    },
    'Logging': {
        'level': 'INFO',
        'file_logging': True,
        'console_logging': False,
    },
}

# Supported file formats
SUPPORTED_FILE_FORMATS = [
    ('All Supported Files', '*.txt;*.md;*.doc;*.docx;*.htm;*.html;*.epub;*.pdf'),
    ('All Files', '*.*'),
]

# Application info
APP_NAME = 'PanDoG'
APP_VERSION = '0.0.1'
APP_AUTHOR = 'Steffen Schultz'
APP_WEBSITE = 'https://m45.dev'
APP_LICENSE = 'MIT License'

# Mapping from pandoc output format to file extension
FORMAT_EXTENSIONS = {
    'asciidoc': 'adoc',
    'asciidoctor': 'adoc',
    'beamer': 'tex',
    'commonmark': 'md',
    'context': 'tex',
    'docbook': 'xml',
    'docbook5': 'xml',
    'docx': 'docx',
    'dzslides': 'html',
    'epub': 'epub',
    'epub3': 'epub',
    'gfm': 'md',
    'html': 'html',
    'html5': 'html',
    'jats': 'xml',
    'latex': 'tex',
    'man': 'man',
    'markdown': 'md',
    'markdown_strict': 'md',
    'mediawiki': 'wiki',
    'odt': 'odt',
    'opml': 'opml',
    'org': 'org',
    'pdf': 'pdf',
    'pptx': 'pptx',
    'revealjs': 'html',
    'rst': 'rst',
    'rtf': 'rtf',
    's5': 'html',
    'slideous': 'html',
    'slidy': 'html',
    'textile': 'textile',
}
