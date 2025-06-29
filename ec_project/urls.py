# ec_project/urls.py

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Users app (only once, using tuple form so Django sees your app_name)
    path(
        'users/',
        include(('users.urls', 'users'), namespace='users')
    ),

    # Webapp
    path(
        'webapp/',
        include(('webapp.urls', 'webapp'), namespace='webapp')
    ),

    # Redirect root → /webapp/
    path('', RedirectView.as_view(url='/webapp/')),
]






