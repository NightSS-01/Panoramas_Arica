from django.conf import settings
from django.db import models
from django.templatetags.static import static


class Actividad(models.Model):
    class Modalidad(models.TextChoices):
        RESERVABLE = 'reservable', 'Reservable'
        DIFUSION = 'difusion', 'Difusión'
        SIN_FINES_DE_LUCRO = 'reservable_sin_fines_de_lucro', 'Reservable sin fines de lucro'

    proveedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='actividades',
        limit_choices_to={'rol': 'proveedor'},
    )
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField()
    modalidad = models.CharField(
        max_length=40, choices=Modalidad.choices, default=Modalidad.RESERVABLE
    )
    ubicacion = models.CharField(max_length=150, blank=True)
    imagen = models.ImageField(upload_to='actividades/', blank=True)
    precio = models.PositiveIntegerField(null=True, blank=True)
    publicada = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada_en']
        verbose_name_plural = 'actividades'

    def __str__(self):
        return self.titulo
    
    @property
    def tiene_precio(self):
        return bool(self.precio)

    @property
    def precio_texto(self):
        if self.precio is None:
            return 'Precio por confirmar'
        if self.precio == 0:
            return 'Sin costo'
        return '$' + f'{self.precio:,}'.replace(',', '.')

    @property
    def primera_disponibilidad(self):
        disponibles = list(self.disponibilidades.all())
        return disponibles[0] if disponibles else None

    @property
    def es_reservable(self):
        if self.modalidad == self.Modalidad.DIFUSION:
            return False
        return any(d.cupos > 0 for d in self.disponibilidades.all())

    @property
    def imagen_url(self):
        if self.imagen:
            return self.imagen.url
        return static('actividades/img/sin-imagen.png')


class Disponibilidad(models.Model):
    actividad = models.ForeignKey(
        Actividad, on_delete=models.CASCADE, related_name='disponibilidades'
    )
    fecha = models.DateField()
    cupos = models.PositiveIntegerField()

    class Meta:
        ordering = ['fecha']
        verbose_name_plural = 'disponibilidades'

    def __str__(self):
        return f'{self.actividad} · {self.fecha} · {self.cupos} cupos'