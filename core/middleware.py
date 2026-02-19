from django.utils import translation


class UserPreferredLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, 'user', None) and request.user.is_authenticated:
            translation.activate(request.user.preferred_language)
            request.LANGUAGE_CODE = request.user.preferred_language
        return self.get_response(request)
