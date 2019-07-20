DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.sqlite3',
    }
}
SECRET_KEY = 'test-only-s3cret'

INSTALLED_APPS = ['rutedata.apps.RutedataConfig', ]