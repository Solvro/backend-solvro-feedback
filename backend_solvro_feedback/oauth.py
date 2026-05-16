from authlib.integrations.django_client import OAuth

oauth = OAuth()
oauth.register(name="solvro-auth")
