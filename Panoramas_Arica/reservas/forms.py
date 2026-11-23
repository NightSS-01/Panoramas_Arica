from django import forms
from django.utils import timezone

from actividades.models import Disponibilidad


class ReservaForm(forms.Form):
    disponibilidad = forms.ModelChoiceField(
        queryset=Disponibilidad.objects.none(),
        label='Fecha',
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    cantidad = forms.IntegerField(
        label='Cantidad de personas',
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, actividad, **kwargs):
        super().__init__(*args, **kwargs)
        campo = self.fields['disponibilidad']
        campo.queryset = actividad.disponibilidades.filter(
            fecha__gte=timezone.localdate(), cupos__gt=0
        )
        campo.label_from_instance = lambda d: f'{d.fecha:%d/%m/%Y} — {d.cupos} cupos disponibles'

    def clean(self):
        datos = super().clean()
        disponibilidad = datos.get('disponibilidad')
        cantidad = datos.get('cantidad')
        if disponibilidad and cantidad and cantidad > disponibilidad.cupos:
            self.add_error('cantidad', f'Solo quedan {disponibilidad.cupos} cupos para esa fecha.')
        return datos