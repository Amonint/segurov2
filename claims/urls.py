from django.urls import path

from . import views

app_name = "claims"

urlpatterns = [
    # Claim management
    path("", views.claim_list, name="claim_list"),
    path("my-claims/", views.my_claims, name="my_claims"),
    path("create/", views.claim_create, name="claim_create"),
    path("<int:pk>/", views.claim_detail, name="claim_detail"),
    path("<int:pk>/edit/", views.claim_edit, name="claim_edit"),
    path("<int:pk>/status/", views.claim_update_status, name="claim_update_status"),
    path("<int:pk>/delete/", views.claim_delete, name="claim_delete"),
    # Validation workflow - New endpoints
    path("<int:pk>/approve/", views.claim_approve, name="claim_approve"),
    path(
        "<int:pk>/request-changes/",
        views.claim_request_changes,
        name="claim_request_changes",
    ),
    path("<int:pk>/reject/", views.claim_reject, name="claim_reject"),
    # Claim documents
    path("<int:pk>/documents/", views.claim_documents, name="claim_documents"),
    path(
        "<int:pk>/documents/upload/",
        views.claim_document_upload,
        name="claim_document_upload",
    ),
    path(
        "<int:pk>/documents/request/",
        views.claim_request_documents,
        name="claim_request_documents",
    ),
    path(
        "documents/<int:pk>/delete/",
        views.claim_document_delete,
        name="claim_document_delete",
    ),
    # Claim settlements
    path("settlements/", views.claim_settlements_list, name="claim_settlements_list"),
    path(
        "<int:claim_pk>/settlement/create/",
        views.claim_settlement_create,
        name="claim_settlement_create",
    ),
    path(
        "settlements/<int:pk>/",
        views.claim_settlement_detail,
        name="claim_settlement_detail",
    ),
    path(
        "settlements/<int:pk>/edit/",
        views.claim_settlement_edit,
        name="claim_settlement_edit",
    ),
    path(
        "settlements/<int:pk>/approve/",
        views.claim_settlement_approve,
        name="claim_settlement_approve",
    ),
    path(
        "settlements/<int:pk>/sign/",
        views.claim_settlement_sign,
        name="claim_settlement_sign",
    ),
    path(
        "settlements/<int:pk>/pay/",
        views.claim_settlement_pay,
        name="claim_settlement_pay",
    ),
]
