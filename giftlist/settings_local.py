DEBUG = True
STATIC_URL = '/static/'

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
print 'Site Root %s' % SITE_ROOT
STATIC_ROOT = ''

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, "../static"),
)