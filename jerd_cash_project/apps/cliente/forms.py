from django import forms
from .models import PerfilCliente
from .models import SolicitudCredito


# ==========================================
# PAÍSES
# ==========================================

PAISES = [
    ('', 'Seleccione un país'),
    ('Argentina', 'Argentina'),
    ('Bolivia', 'Bolivia'),
    ('Brasil', 'Brasil'),
    ('Chile', 'Chile'),
    ('Colombia', 'Colombia'),
    ('Costa Rica', 'Costa Rica'),
    ('Cuba', 'Cuba'),
    ('Ecuador', 'Ecuador'),
    ('El Salvador', 'El Salvador'),
    ('Guatemala', 'Guatemala'),
    ('Honduras', 'Honduras'),
    ('México', 'México'),
    ('Nicaragua', 'Nicaragua'),
    ('Panamá', 'Panamá'),
    ('Paraguay', 'Paraguay'),
    ('Perú', 'Perú'),
    ('República Dominicana', 'República Dominicana'),
    ('Uruguay', 'Uruguay'),
    ('Venezuela', 'Venezuela'),
]


# ==========================================
# CIUDADES POR PAÍS
# ==========================================

CIUDADES_POR_PAIS = {

    'Argentina': [
        'Buenos Aires',
        'Córdoba',
        'Rosario',
        'Mendoza',
        'La Plata',
        'Mar del Plata',
        'Salta',
        'Santa Fe',
        'San Miguel de Tucumán',
        'Neuquén',
    ],

    'Bolivia': [
        'La Paz',
        'Santa Cruz de la Sierra',
        'Cochabamba',
        'Sucre',
        'Oruro',
        'Tarija',
        'Potosí',
        'Trinidad',
        'Cobija',
    ],

    'Brasil': [
        'São Paulo',
        'Rio de Janeiro',
        'Brasília',
        'Salvador',
        'Fortaleza',
        'Belo Horizonte',
        'Manaus',
        'Curitiba',
        'Recife',
        'Porto Alegre',
    ],

    'Chile': [
        'Santiago',
        'Valparaíso',
        'Concepción',
        'La Serena',
        'Antofagasta',
        'Temuco',
        'Rancagua',
        'Talca',
        'Arica',
        'Puerto Montt',
    ],

    'Colombia': [
        'Bogotá',
        'Medellín',
        'Cali',
        'Barranquilla',
        'Cartagena',
        'Bucaramanga',
        'Pereira',
        'Santa Marta',
        'Manizales',
        'Cúcuta',
        'Ibagué',
        'Villavicencio',
        'Pasto',
        'Montería',
        'Neiva',
        'Armenia',
        'Valledupar',
        'Sincelejo',
        'Popayán',
        'Tunja',
    ],

    'Costa Rica': [
        'San José',
        'Alajuela',
        'Cartago',
        'Heredia',
        'Liberia',
        'Puntarenas',
        'Limón',
    ],

    'Cuba': [
        'La Habana',
        'Santiago de Cuba',
        'Camagüey',
        'Holguín',
        'Santa Clara',
        'Guantánamo',
        'Bayamo',
        'Cienfuegos',
    ],

    'Ecuador': [
        'Quito',
        'Guayaquil',
        'Cuenca',
        'Santo Domingo',
        'Machala',
        'Manta',
        'Portoviejo',
        'Loja',
        'Ambato',
        'Riobamba',
    ],

    'El Salvador': [
        'San Salvador',
        'Santa Ana',
        'San Miguel',
        'Soyapango',
        'Santa Tecla',
        'Mejicanos',
        'Sonsonate',
    ],

    'Guatemala': [
        'Ciudad de Guatemala',
        'Mixco',
        'Villa Nueva',
        'Quetzaltenango',
        'Escuintla',
        'Cobán',
        'Huehuetenango',
        'Antigua Guatemala',
    ],

    'Honduras': [
        'Tegucigalpa',
        'San Pedro Sula',
        'La Ceiba',
        'Choloma',
        'Comayagua',
        'Puerto Cortés',
        'El Progreso',
    ],

    'México': [
        'Ciudad de México',
        'Guadalajara',
        'Monterrey',
        'Puebla',
        'Tijuana',
        'Ciudad Juárez',
        'León',
        'Mérida',
        'Cancún',
        'Querétaro',
        'Toluca',
        'Chihuahua',
        'Aguascalientes',
        'Hermosillo',
        'Mexicali',
    ],

    'Nicaragua': [
        'Managua',
        'León',
        'Masaya',
        'Matagalpa',
        'Chinandega',
        'Granada',
        'Estelí',
        'Jinotepe',
    ],

    'Panamá': [
        'Ciudad de Panamá',
        'San Miguelito',
        'Colón',
        'David',
        'La Chorrera',
        'Santiago de Veraguas',
        'Chitré',
    ],

    'Paraguay': [
        'Asunción',
        'Ciudad del Este',
        'San Lorenzo',
        'Luque',
        'Capiatá',
        'Lambaré',
        'Fernando de la Mora',
    ],

    'Perú': [
        'Lima',
        'Arequipa',
        'Trujillo',
        'Chiclayo',
        'Piura',
        'Cusco',
        'Iquitos',
        'Huancayo',
        'Tacna',
        'Chimbote',
    ],

    'República Dominicana': [
        'Santo Domingo',
        'Santiago de los Caballeros',
        'Santo Domingo Este',
        'La Romana',
        'San Pedro de Macorís',
        'Puerto Plata',
        'San Cristóbal',
    ],

    'Uruguay': [
        'Montevideo',
        'Salto',
        'Ciudad de la Costa',
        'Paysandú',
        'Las Piedras',
        'Rivera',
        'Maldonado',
        'Tacuarembó',
    ],

    'Venezuela': [
        'Caracas',
        'Maracaibo',
        'Valencia',
        'Barquisimeto',
        'Maracay',
        'Ciudad Guayana',
        'Maturín',
        'Barcelona',
        'Puerto La Cruz',
        'Cumaná',
    ],
}


class PerfilClienteForm(forms.ModelForm):

    primer_nombre = forms.CharField(
        required=True,
        max_length=100,
        label='Primer nombre'
    )

    segundo_nombre = forms.CharField(
        required=False,
        max_length=100,
        label='Segundo nombre'
    )

    primer_apellido = forms.CharField(
        required=True,
        max_length=100,
        label='Primer apellido'
    )

    segundo_apellido = forms.CharField(
        required=False,
        max_length=100,
        label='Segundo apellido'
    )

    email = forms.EmailField(
        required=True,
        label='Correo electrónico'
    )

    nacionalidad = forms.ChoiceField(
        required=True,
        label='Nacionalidad',
        choices=PAISES
    )

    ciudad_nacimiento = forms.ChoiceField(
        required=True,
        label='Ciudad de nacimiento',
        choices=[('', 'Seleccione primero un país')]
    )

    pais_residencia = forms.ChoiceField(
        required=True,
        label='País de residencia',
        choices=PAISES
    )

    ciudad_residencia = forms.ChoiceField(
        required=True,
        label='Ciudad de residencia',
        choices=[('', 'Seleccione primero un país')]
    )

    telefono = forms.CharField(
        required=True,
        max_length=20,
        label='Teléfono'
    )

    direccion = forms.CharField(
        required=True,
        max_length=200,
        label='Dirección'
    )

    contacto_respaldo_nombre = forms.CharField(
        required=True,
        max_length=150,
        label='Nombre completo'
    )

    contacto_respaldo_telefono = forms.CharField(
        required=True,
        max_length=20,
        label='Teléfono'
    )

    contacto_respaldo_parentesco = forms.CharField(
        required=True,
        max_length=50,
        label='Parentesco'
    )

    ingresos_mensuales = forms.DecimalField(
        required=True,
        min_value=0.01,
        label='Ingresos mensuales',
        widget=forms.NumberInput(attrs={
            'placeholder': 'Ej. 2000000',
            'min': '0.01',
            'step': '0.01'
        })
    )

    gastos_mensuales = forms.DecimalField(
        required=True,
        min_value=0.01,
        label='Gastos mensuales',
        widget=forms.NumberInput(attrs={
            'placeholder': 'Ej. 800000',
            'min': '0.01',
            'step': '0.01'
        })
    )

    class Meta:
        model = PerfilCliente

        fields = [
            'nacionalidad',
            'ciudad_nacimiento',
            'pais_residencia',
            'ciudad_residencia',
            'telefono',
            'direccion',
            'contacto_respaldo_nombre',
            'contacto_respaldo_telefono',
            'contacto_respaldo_parentesco',
            'ingresos_mensuales',
            'gastos_mensuales',
        ]

    def __init__(self, *args, **kwargs):

        self.usuario = kwargs.pop('usuario', None)

        super().__init__(*args, **kwargs)

        # ==========================================
        # CIUDADES DE NACIMIENTO
        # ==========================================

        pais_nacimiento = None

        if self.is_bound:
            pais_nacimiento = self.data.get('nacionalidad')
        elif self.instance:
            pais_nacimiento = self.instance.nacionalidad

        ciudades_nacimiento = CIUDADES_POR_PAIS.get(
            pais_nacimiento,
            []
        )

        self.fields['ciudad_nacimiento'].choices = [
            ('', 'Seleccione una ciudad')
        ] + [
            (ciudad, ciudad)
            for ciudad in ciudades_nacimiento
        ]

        # ==========================================
        # CIUDADES DE RESIDENCIA
        # ==========================================

        pais_residencia = None

        if self.is_bound:
            pais_residencia = self.data.get('pais_residencia')
        elif self.instance:
            pais_residencia = self.instance.pais_residencia

        ciudades_residencia = CIUDADES_POR_PAIS.get(
            pais_residencia,
            []
        )

        self.fields['ciudad_residencia'].choices = [
            ('', 'Seleccione una ciudad')
        ] + [
            (ciudad, ciudad)
            for ciudad in ciudades_residencia
        ]

        # ==========================================
        # ESTILOS
        # ==========================================

        clases = (
            'w-full px-4 py-2.5 border border-gray-300 rounded-lg '
            'focus:ring-2 focus:ring-blue-500 '
            'focus:border-blue-500 '
            'outline-none transition'
        )

        for nombre, campo in self.fields.items():

            campo.widget.attrs.update({
                'class': clases
            })

        # ==========================================
        # DATOS DEL USUARIO
        # ==========================================

        if self.usuario:

            self.fields['primer_nombre'].initial = (
                self.usuario.first_name
            )

            self.fields['segundo_nombre'].initial = (
                self.usuario.segundo_nombre
            )

            self.fields['primer_apellido'].initial = (
                self.usuario.primer_apellido
            )

            self.fields['segundo_apellido'].initial = (
                self.usuario.segundo_apellido
            )

            self.fields['email'].initial = (
                self.usuario.email
            )

    def save(self, commit=True):

        perfil = super().save(commit=False)

        if self.usuario:

            self.usuario.first_name = (
                self.cleaned_data['primer_nombre']
            )

            self.usuario.segundo_nombre = (
                self.cleaned_data['segundo_nombre']
            )

            self.usuario.primer_apellido = (
                self.cleaned_data['primer_apellido']
            )

            self.usuario.segundo_apellido = (
                self.cleaned_data['segundo_apellido']
            )

            self.usuario.email = (
                self.cleaned_data['email']
            )

            self.usuario.save()

        if commit:
            perfil.save()

        return perfil

class SolicitudCreditoForm(forms.ModelForm):

    class Meta:

        model = SolicitudCredito

        fields = [
            'monto_solicitado',
            'plazo_meses',
            'cedula',
            'recibo',
            'certificacion_bancaria',
            'extracto_bancario_1',
            'extracto_bancario_2',
            'extracto_bancario_3',
        ]

        widgets = {

            'monto_solicitado': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-4 py-2',
                'placeholder': 'Ingrese el monto solicitado',
                'min': '1',
            }),

            'plazo_meses': forms.Select(
                choices=[
                    (6, '6 meses'),
                    (12, '12 meses'),
                    (18, '18 meses'),
                    (24, '24 meses'),
                    (36, '36 meses'),
                ],
                attrs={
                    'class': 'w-full border rounded-lg px-4 py-2',
                }
            ),

            'cedula': forms.ClearableFileInput(attrs={
                'class': 'w-full border rounded-lg px-4 py-2',
                'accept': '.pdf',
            }),

            'recibo': forms.ClearableFileInput(attrs={
                'class': 'w-full border rounded-lg px-4 py-2',
                'accept': '.pdf',
            }),

            'certificacion_bancaria': forms.ClearableFileInput(attrs={
                'class': 'w-full border rounded-lg px-4 py-2',
                'accept': '.pdf',
            }),

            'extracto_bancario_1': forms.ClearableFileInput(attrs={
                'class': 'w-full border rounded-lg px-4 py-2',
                'accept': '.pdf',
                'required': True,
            }),

            'extracto_bancario_2': forms.ClearableFileInput(attrs={
                'class': 'w-full border rounded-lg px-4 py-2',
                'accept': '.pdf',
                'required': True,
            }),

            'extracto_bancario_3': forms.ClearableFileInput(attrs={
                'class': 'w-full border rounded-lg px-4 py-2',
                'accept': '.pdf',
                'required': True,
            }),
        }

    def clean_cedula(self):

        archivo = self.cleaned_data.get('cedula')

        if archivo:

            if not archivo.name.lower().endswith('.pdf'):
                raise forms.ValidationError(
                    'La cédula debe estar en formato PDF.'
                )

            if archivo.content_type != 'application/pdf':
                raise forms.ValidationError(
                    'El archivo de la cédula debe ser un PDF válido.'
                )

        return archivo

    def clean_recibo(self):

        archivo = self.cleaned_data.get('recibo')

        if archivo:

            if not archivo.name.lower().endswith('.pdf'):
                raise forms.ValidationError(
                    'El recibo debe estar en formato PDF.'
                )

            if archivo.content_type != 'application/pdf':
                raise forms.ValidationError(
                    'El archivo del recibo debe ser un PDF válido.'
                )

        return archivo

    def clean_certificacion_bancaria(self):

        archivo = self.cleaned_data.get('certificacion_bancaria')

        if archivo:

            if not archivo.name.lower().endswith('.pdf'):
                raise forms.ValidationError(
                    'La certificación bancaria debe estar en formato PDF.'
                )

            if archivo.content_type != 'application/pdf':
                raise forms.ValidationError(
                    'El archivo de la certificación bancaria debe ser un PDF válido.'
                )

        return archivo

    def clean_extracto_bancario_1(self):

        return self.validar_extracto(
            self.cleaned_data.get('extracto_bancario_1')
        )

    def clean_extracto_bancario_2(self):

        return self.validar_extracto(
            self.cleaned_data.get('extracto_bancario_2')
        )

    def clean_extracto_bancario_3(self):

        return self.validar_extracto(
            self.cleaned_data.get('extracto_bancario_3')
        )

    def validar_extracto(self, archivo):

        if not archivo:
            raise forms.ValidationError(
                'Debe adjuntar este extracto bancario.'
            )

        if not archivo.name.lower().endswith('.pdf'):
            raise forms.ValidationError(
                'El extracto bancario debe estar en formato PDF.'
            )

        if archivo.content_type != 'application/pdf':
            raise forms.ValidationError(
                'El archivo debe ser un PDF válido.'
            )

        return archivo