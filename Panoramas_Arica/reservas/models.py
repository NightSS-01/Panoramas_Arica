from django.conf import settings
from django.db import models


class Reserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente de pago'
        PAGADA = 'pagada', 'Pagada'
        CONFIRMADA = 'confirmada', 'Confirmada'
        RECHAZADA = 'rechazada', 'Pago rechazado'
        ANULADA = 'anulada', 'Pago anulado'
        SIN_CUPOS = 'sin_cupos', 'Pagada sin cupos'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reservas'
    )
    actividad = models.ForeignKey(
        'actividades.Actividad', on_delete=models.SET_NULL, null=True, related_name='reservas'
    )
    disponibilidad = models.ForeignKey(
        'actividades.Disponibilidad', on_delete=models.SET_NULL, null=True, related_name='reservas'
    )
    # Copias para que la reserva siga siendo legible si el proveedor borra la actividad
    actividad_titulo = models.CharField(max_length=120)
    fecha = models.DateField()
    cantidad = models.PositiveSmallIntegerField()
    monto = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    buy_order = models.CharField(max_length=26, unique=True)
    token = models.CharField(max_length=64, blank=True)
    codigo_autorizacion = models.CharField(max_length=20, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creada_en']

    def __str__(self):
        return f'{self.buy_order} · {self.actividad_titulo} · {self.get_estado_display()}'

    @property
    def exitosa(self):
        return self.estado in (self.Estado.PAGADA, self.Estado.CONFIRMADA)

    @property
    def monto_texto(self):
        if self.monto == 0:
            return 'Sin costo'
        return '$' + f'{self.monto:,}'.replace(',', '.')