from django.urls import path

from . import views

app_name = "policies"

urlpatterns = [
    # Policy management
    path("", views.policy_list, name="policy_list"),
    path("create/", views.policy_create, name="policy_create"),
    path("<int:pk>/", views.policy_detail, name="policy_detail"),
    path("<int:pk>/edit/", views.policy_edit, name="policy_edit"),
    path("<int:pk>/delete/", views.policy_delete, name="policy_delete"),
    path("<int:pk>/renew/", views.policy_renew, name="policy_renew"),
    # Policy documents
    path("<int:pk>/documents/", views.policy_documents, name="policy_documents"),
    path(
        "<int:pk>/documents/upload/",
        views.policy_document_upload,
        name="policy_document_upload",
    ),
    path(
        "documents/<int:document_pk>/edit/",
        views.policy_document_edit,
        name="policy_document_edit",
    ),
    path(
        "documents/<int:document_pk>/delete/",
        views.policy_document_delete,
        name="policy_document_delete",
    ),
    path(
        "documents/<int:document_pk>/download/",
        views.policy_document_download,
        name="policy_document_download",
    ),
    path(
        "documents/<int:document_pk>/view/",
        views.policy_document_view,
        name="policy_document_view",
    ),
    path(
        "documents/<int:document_pk>/versions/",
        views.policy_document_versions,
        name="policy_document_versions",
    ),
    path(
        "documents/<int:document_pk>/new-version/",
        views.policy_document_new_version,
        name="policy_document_new_version",
    ),
    # Bulk actions
    path("bulk-action/", views.policy_bulk_action, name="policy_bulk_action"),
]
