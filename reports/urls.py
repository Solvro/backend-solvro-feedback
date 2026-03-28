from django.urls import path

from .views import PublicReportCreateView

urlpatterns = [
    path(
        "report/<uuid:app_id>", PublicReportCreateView.as_view(), name="report-create"
    ),
]
