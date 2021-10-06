class BaseConfig():
   API_PREFIX = '/api'
   TESTING = False
   DEBUG = False


class DevConfig(BaseConfig):
   FLASK_ENV = 'development'
   DEBUG = True

   # we can add constants here
   #FIELD_NAME = "field-value"


class ProductionConfig(BaseConfig):
   FLASK_ENV = 'production'

   # we can add constants here
   #FIELD_NAME = "field-value"


class TestConfig(BaseConfig):
   FLASK_ENV = 'development'
   TESTING = True
   DEBUG = True
   
   # we can add constants here
   #FIELD_NAME = "field-value"