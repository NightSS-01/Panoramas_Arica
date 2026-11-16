from django import forms
from django.db import transaction
from django.utils import timezone

from .models import Actividad, Disponibilidad


class ActividadForm(forms.ModelForm):
    fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
    )
    cupos = forms.IntegerField(
        required=False, min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Ej. 12', 'min': 0}),
    )

    class Meta:
        model = Actividad
        fields = ['titulo', 'descripcion', 'modalidad', 'precio', 'imagen']
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Ej. Ruta fotográfica por el humedal'}),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe la experiencia, qué incluye y qué podrán descubrir…',
            }),
            'precio': forms.NumberInput(attrs={'placeholder': '$ CLP', 'min': 0}),
            'imagen': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if nombre != 'imagen':
                campo.widget.attrs['class'] = 'campo__control'
        self.fields['imagen'].widget.attrs.update(
            {'hidden': True, 'accept': 'image/jpeg,image/png'}
        )

        # Al editar: precargar fecha y cupos de la primera disponibilidad
        self._fecha_original = None
        if self.instance.pk:
            disponibilidad = self.instance.primera_disponibilidad
            if disponibilidad:
                self._fecha_original = disponibilidad.fecha
                self.initial['fecha'] = disponibilidad.fecha
                self.initial['cupos'] = disponibilidad.cupos

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha < timezone.localdate() and fecha != self._fecha_original:
            raise forms.ValidationError('La fecha no puede ser anterior a hoy.')
        return fecha

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen and imagen.size > 2 * 1024 * 1024:
            raise forms.ValidationError('La imagen no puede pesar más de 2 MB.')
        return imagen

    def clean(self):
        datos = super().clean()
        modalidad = datos.get('modalidad')
        fecha = datos.get('fecha')
        cupos = datos.get('cupos')

        if modalidad and modalidad != Actividad.Modalidad.DIFUSION:
            if not fecha:
                self.add_error('fecha', 'Indica la fecha de la actividad.')
            if not cupos:
                self.add_error('cupos', 'Indica al menos 1 cupo.')
        elif cupos and not fecha:
            self.add_error('fecha', 'Indica la fecha para los cupos que ingresaste.')
        return datos

    @transaction.atomic
    def guardar(self, proveedor):
        actividad = super().save(commit=False)
        actividad.proveedor = proveedor
        actividad.save()

        fecha = self.cleaned_data.get('fecha')
        cupos = self.cleaned_data.get('cupos') or 0
        existente = actividad.disponibilidades.first()

        if fecha:
            if existente:
                existente.fecha = fecha
                existente.cupos = cupos
                existente.save()
            else:
                Disponibilidad.objects.create(actividad=actividad, fecha=fecha, cupos=cupos)
        elif existente:
            existente.delete()
        return actividad