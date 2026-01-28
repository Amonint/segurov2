from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import UserProfile


class Notification(models.Model):
    """
    Model for system notifications
    """

    # Notification type choices
    NOTIFICATION_TYPE_CHOICES = [
        ("policy_expiring", _("Póliza por vencer")),
        ("policy_expired", _("Póliza vencida")),
        ("payment_due", _("Pago pendiente")),
        ("invoice_overdue", _("Factura vencida")),
        ("claim_update", _("Actualización de siniestro")),
        ("claim_overdue", _("Siniestro atrasado")),
        ("document_required", _("Documento requerido")),
        ("document_overdue", _("Documento vencido")),
        ("maintenance_required", _("Mantenimiento requerido")),
        ("system_alert", _("Alerta del sistema")),
        ("alert", _("Alerta general")),
    ]

    # Priority choices
    PRIORITY_CHOICES = [
        ("low", _("Baja")),
        ("normal", _("Normal")),
        ("high", _("Alta")),
        ("urgent", _("Urgente")),
    ]

    # Notification fields
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        verbose_name=_("Usuario"),
        related_name="notifications",
    )
    notification_type = models.CharField(
        _("Tipo de notificación"), max_length=20, choices=NOTIFICATION_TYPE_CHOICES
    )
    title = models.CharField(_("Título"), max_length=255)
    message = models.TextField(_("Mensaje"))
    link = models.URLField(_("Enlace"), blank=True)
    is_read = models.BooleanField(_("¿Leída?"), default=False)
    read_at = models.DateTimeField(_("Fecha de lectura"), null=True, blank=True)
    priority = models.CharField(
        _("Prioridad"), max_length=10, choices=PRIORITY_CHOICES, default="normal"
    )
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("Notificación")
        verbose_name_plural = _("Notificaciones")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["is_read", "priority"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"

    def mark_as_read(self):
        """
        Mark notification as read
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    @staticmethod
    def create_notification(
        user, notification_type, title, message, priority="normal", link=""
    ):
        """
        Create a new notification
        """
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            link=link,
        )

    @staticmethod
    def get_unread_count(user):
        """
        Get count of unread notifications for a user
        """
        return Notification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    def bulk_mark_as_read(user, notification_ids=None):
        """
        Mark multiple notifications as read
        """
        queryset = Notification.objects.filter(user=user, is_read=False)
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)

        return queryset.update(is_read=True)


class EmailTemplate(models.Model):
    """
    Email templates for automated notifications
    """

    # Template type choices
    TEMPLATE_TYPE_CHOICES = [
        ("claim_reported", _("Siniestro Reportado")),
        ("claim_updated", _("Siniestro Actualizado")),
        ("claim_liquidated", _("Siniestro Liquidado")),
        ("claim_paid", _("Siniestro Pagado")),
        ("claim_rejected", _("Siniestro Rechazado")),
        ("policy_expiring", _("Póliza por Vencer")),
        ("policy_expired", _("Póliza Vencida")),
        ("payment_due", _("Pago Pendiente")),
        ("payment_overdue", _("Pago Vencido")),
        ("payment_completed", _("Pago Completado")),
        ("invoice_generated", _("Factura Generada")),
        ("invoice_overdue", _("Factura Vencida")),
        ("claim_overdue", _("Siniestro Atrasado")),
        ("document_overdue", _("Documento Vencido")),
        ("maintenance_required", _("Mantenimiento Requerido")),
        ("settlement_signed", _("Finiquito Firmado")),
        ("system_alert", _("Alerta del Sistema")),
        ("broker_notification", _("Notificación a Broker")),
        ("insurer_notification", _("Notificación a Aseguradora")),
    ]

    # Recipient type choices
    RECIPIENT_TYPE_CHOICES = [
        ("user", _("Usuario del Sistema")),
        ("broker", _("Broker")),
        ("insurer", _("Aseguradora")),
        ("client", _("Cliente")),
        ("financial", _("Gerencia Financiera")),
    ]

    name = models.CharField(_("Nombre"), max_length=100, unique=True)
    template_type = models.CharField(
        _("Tipo de Plantilla"), max_length=30, choices=TEMPLATE_TYPE_CHOICES
    )
    recipient_type = models.CharField(
        _("Tipo de Destinatario"), max_length=20, choices=RECIPIENT_TYPE_CHOICES
    )
    subject = models.CharField(
        _("Asunto"),
        max_length=255,
        help_text=_("Asunto del email - puede incluir variables ej: {{claim_number}}"),
    )
    body_html = models.TextField(
        _("Cuerpo HTML"),
        help_text=_("Cuerpo del email en HTML - puede incluir variables"),
    )
    body_text = models.TextField(
        _("Cuerpo Texto Plano"),
        blank=True,
        help_text=_("Versión texto plano (opcional)"),
    )
    is_active = models.BooleanField(_("Activo"), default=True)
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Actualizado"), auto_now=True)
    created_by = models.ForeignKey(
        UserProfile, on_delete=models.SET_NULL, null=True, verbose_name=_("Creado por")
    )

    class Meta:
        verbose_name = _("Plantilla de Email")
        verbose_name_plural = _("Plantillas de Email")
        ordering = ["template_type", "name"]

    def __str__(self):
        return f"{self.get_template_type_display()} - {self.name}"

    def render_subject(self, context=None):
        """
        Render subject with context variables
        """
        if not context:
            context = {}
        try:
            from django.template import Context, Template

            template = Template(self.subject)
            return template.render(Context(context))
        except Exception:
            return self.subject

    def render_body_html(self, context=None):
        """
        Render HTML body with context variables
        """
        if not context:
            context = {}
        try:
            from django.template import Context, Template

            template = Template(self.body_html)
            return template.render(Context(context))
        except Exception:
            return self.body_html

    def render_body_text(self, context=None):
        """
        Render text body with context variables
        """
        if not context:
            context = {}
        try:
            if self.body_text:
                from django.template import Context, Template

                template = Template(self.body_text)
                return template.render(Context(context))
            else:
                # Convert HTML to text if no text version exists
                import re

                html = self.render_body_html(context)
                # Simple HTML to text conversion
                text = re.sub(r"<[^>]+>", "", html)
                text = re.sub(r"\s+", " ", text).strip()
                return text
        except Exception:
            return self.body_text or "Contenido no disponible"


class EmailLog(models.Model):
    """
    Log of sent emails (simulated)
    """

    # Status choices
    STATUS_CHOICES = [
        ("sent", _("Enviado")),
        ("failed", _("Fallido")),
        ("pending", _("Pendiente")),
        ("simulated", _("Simulado")),
    ]

    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        verbose_name=_("Plantilla"),
        related_name="email_logs",
    )
    recipient_email = models.EmailField(_("Email del Destinatario"))
    recipient_name = models.CharField(
        _("Nombre del Destinatario"), max_length=255, blank=True
    )
    subject = models.CharField(_("Asunto"), max_length=255)
    status = models.CharField(
        _("Estado"), max_length=10, choices=STATUS_CHOICES, default="pending"
    )
    sent_at = models.DateTimeField(_("Enviado"), null=True, blank=True)
    error_message = models.TextField(_("Mensaje de Error"), blank=True)
    context_data = models.JSONField(
        _("Datos del Contexto"),
        help_text=_("Variables utilizadas en la plantilla"),
        default=dict,
    )

    # Related objects (optional)
    claim = models.ForeignKey(
        "claims.Claim",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Siniestro Relacionado"),
    )
    policy = models.ForeignKey(
        "policies.Policy",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Póliza Relacionada"),
    )
    invoice = models.ForeignKey(
        "invoices.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Factura Relacionada"),
    )

    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    created_by = models.ForeignKey(
        UserProfile, on_delete=models.SET_NULL, null=True, verbose_name=_("Creado por")
    )

    class Meta:
        verbose_name = _("Log de Email")
        verbose_name_plural = _("Logs de Email")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["recipient_email"]),
        ]

    def __str__(self):
        return f"{self.template.name} -> {self.recipient_email} ({self.get_status_display()})"

    def simulate_send(self):
        """
        Simulate email sending (for development/testing)
        """
        import time

        from django.utils import timezone

        # Simulate processing time
        time.sleep(0.1)

        # Random success/failure simulation
        import random

        success = random.choice([True, True, True, False])  # 75% success rate

        if success:
            self.status = "simulated"
            self.sent_at = timezone.now()
            self.save()
            return True, "Email simulado enviado exitosamente"
        else:
            self.status = "failed"
            self.error_message = "Error simulado: conexión rechazada"
            self.save()
            return False, self.error_message

    @staticmethod
    def send_email(
        template_type,
        recipient_email,
        recipient_name="",
        context=None,
        claim=None,
        policy=None,
        invoice=None,
        created_by=None,
    ):
        """
        Send email using template (simulated)
        """
        if context is None:
            context = {}

        try:
            # Get active template
            template = EmailTemplate.objects.filter(
                template_type=template_type, is_active=True
            ).first()

            if not template:
                return False, f"No se encontró plantilla activa para {template_type}"

            # Create log entry
            log = EmailLog.objects.create(
                template=template,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                subject=template.render_subject(context),
                claim=claim,
                policy=policy,
                invoice=invoice,
                context_data=context,
                created_by=created_by,
            )

            # Simulate sending
            success, message = log.simulate_send()

            return success, message

        except Exception as e:
            return False, f"Error al enviar email: {str(e)}"


class Alert(models.Model):
    """
    Model for automated alerts
    """

    ALERT_TYPE_CHOICES = [
        ("policy_expiring", _("Póliza por vencer")),
        ("policy_expired", _("Póliza vencida")),
        ("invoice_overdue", _("Factura vencida")),
        ("claim_overdue", _("Siniestro atrasado")),
        ("document_overdue", _("Documento vencido")),
        ("payment_due", _("Pago próximo")),
        ("maintenance_required", _("Mantenimiento requerido")),
        ("system_alert", _("Alerta del sistema")),
    ]

    FREQUENCY_CHOICES = [
        ("daily", _("Diario")),
        ("weekly", _("Semanal")),
        ("monthly", _("Mensual")),
        ("realtime", _("Tiempo real")),
    ]

    name = models.CharField(_("Nombre de la alerta"), max_length=255)
    alert_type = models.CharField(
        _("Tipo de alerta"), max_length=20, choices=ALERT_TYPE_CHOICES
    )
    description = models.TextField(_("Descripción"), blank=True)

    # Conditions
    conditions = models.JSONField(
        _("Condiciones"),
        default=dict,
        help_text=_("Condiciones JSON para activar la alerta"),
    )

    # Recipients
    recipients = models.ManyToManyField(
        UserProfile, verbose_name=_("Destinatarios"), related_name="alerts", blank=True
    )
    email_recipients = models.TextField(
        _("Emails adicionales"), blank=True, help_text=_("Emails separados por comas")
    )

    # Scheduling
    frequency = models.CharField(
        _("Frecuencia"), max_length=10, choices=FREQUENCY_CHOICES, default="daily"
    )
    is_active = models.BooleanField(_("Activa"), default=True)

    # Timing
    last_run = models.DateTimeField(_("Última ejecución"), null=True, blank=True)
    next_run = models.DateTimeField(_("Próxima ejecución"), null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Creado por"),
        related_name="created_alerts",
    )
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Alerta")
        verbose_name_plural = _("Alertas")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_alert_type_display()})"

    def should_run(self):
        """Check if alert should run based on frequency"""
        if not self.is_active:
            return False

        if self.frequency == "realtime":
            return True

        if not self.last_run:
            return True

        now = timezone.now()

        if self.frequency == "daily":
            return (now - self.last_run).days >= 1
        elif self.frequency == "weekly":
            return (now - self.last_run).days >= 7
        elif self.frequency == "monthly":
            return (now - self.last_run).days >= 30

        return False

    def execute(self):
        """Execute the alert and create notifications"""
        from .tasks import execute_alert

        # Update last run time
        self.last_run = timezone.now()
        self.save()

        # Execute the alert logic
        return execute_alert(self)

    def get_email_list(self):
        """Get list of email addresses for this alert"""
        emails = []

        # Add user emails
        for user in self.recipients.filter(is_active=True):
            if user.email:
                emails.append(user.email)

        # Add additional emails
        if self.email_recipients:
            additional_emails = [
                email.strip() for email in self.email_recipients.split(",")
            ]
            emails.extend(additional_emails)

        return list(set(emails))  # Remove duplicates
