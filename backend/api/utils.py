from rest_framework_simplejwt.tokens import RefreshToken


def custom_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return {'auth_token': access_token}
