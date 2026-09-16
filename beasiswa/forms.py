"""
forms.py - Form Django untuk sistem seleksi beasiswa
======================================================
Berisi semua form yang digunakan pada aplikasi beasiswa,
termasuk form data siswa, penilaian, dan data training.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Siswa, PenilaianBeasiswa, DataTraining


# ============================================================
# FORM 1: LOGIN (Menggunakan AuthenticationForm bawaan Django)
# ============================================================
class LoginForm(AuthenticationForm):
    """
    Form login menggunakan AuthenticationForm dari Django.
    Menambahkan styling Bootstrap 5 pada field input.
    """
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={
            'class'      : 'form-control form-control-lg',
            'placeholder': 'Masukkan username',
            'autofocus'  : True,
            'id'         : 'id_username',
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class'      : 'form-control form-control-lg',
            'placeholder': 'Masukkan password',
            'id'         : 'id_password',
        })
    )


# ============================================================
# FORM 2: DATA SISWA
# ============================================================
class SiswaForm(forms.ModelForm):
    """
    Form untuk input/edit data pribadi siswa.
    Memetakan langsung ke model Siswa.
    """

    class Meta:
        model  = Siswa
        fields = ['nis', 'nama', 'kelas', 'jenis_kelamin', 'alamat', 'no_hp']
        widgets = {
            'nis': forms.TextInput(attrs={
                'class'      : 'form-control',
                'placeholder': 'Contoh: 2024001',
                'id'         : 'id_nis',
            }),
            'nama': forms.TextInput(attrs={
                'class'      : 'form-control',
                'placeholder': 'Nama lengkap siswa',
                'id'         : 'id_nama',
            }),
            'kelas': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_kelas',
            }),
            'jenis_kelamin': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_jenis_kelamin',
            }),
            'alamat': forms.Textarea(attrs={
                'class'      : 'form-control',
                'placeholder': 'Alamat lengkap siswa',
                'rows'       : 3,
                'id'         : 'id_alamat',
            }),
            'no_hp': forms.TextInput(attrs={
                'class'      : 'form-control',
                'placeholder': 'Contoh: 081234567890',
                'id'         : 'id_no_hp',
            }),
        }
        labels = {
            'nis'           : 'NIS (Nomor Induk Siswa)',
            'nama'          : 'Nama Lengkap',
            'kelas'         : 'Kelas',
            'jenis_kelamin' : 'Jenis Kelamin',
            'alamat'        : 'Alamat Rumah',
            'no_hp'         : 'Nomor HP/WA',
        }


# ============================================================
# FORM 3: DATA PENILAIAN BEASISWA
# ============================================================
class PenilaianForm(forms.ModelForm):
    """
    Form untuk input/edit data kriteria penilaian beasiswa.
    Dipisah menjadi 4 bagian: Akademik, Prestasi, Ekonomi, Sosial.
    Preprocessing (klasifikasi kategori) dilakukan otomatis di model.save()
    """

    class Meta:
        model  = PenilaianBeasiswa
        fields = [
            # Akademik
            'nilai_rata_rata', 'ranking_kelas', 'persentase_hadir',
            # Prestasi
            'tingkat_prestasi', 'keaktifan_organisasi',
            # Ekonomi
            'penghasilan_ortu', 'jumlah_tanggungan', 'status_rumah', 'memiliki_kip',
            # Sosial
            'jarak_rumah',
        ]
        widgets = {
            # ---- Akademik ----
            'nilai_rata_rata': forms.NumberInput(attrs={
                'class': 'form-control',
                'step' : '0.01',
                'min'  : '0',
                'max'  : '100',
                'placeholder': 'Contoh: 85.50',
                'id'   : 'id_nilai_rata_rata',
            }),
            'ranking_kelas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min'  : '1',
                'placeholder': 'Contoh: 5',
                'id'   : 'id_ranking_kelas',
            }),
            'persentase_hadir': forms.NumberInput(attrs={
                'class': 'form-control',
                'step' : '0.01',
                'min'  : '0',
                'max'  : '100',
                'placeholder': 'Contoh: 95.00',
                'id'   : 'id_persentase_hadir',
            }),

            # ---- Prestasi ----
            'tingkat_prestasi': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_tingkat_prestasi',
            }),
            'keaktifan_organisasi': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_keaktifan_organisasi',
            }),

            # ---- Ekonomi ----
            'penghasilan_ortu': forms.NumberInput(attrs={
                'class': 'form-control',
                'min'  : '0',
                'placeholder': 'Contoh: 1500000',
                'id'   : 'id_penghasilan_ortu',
            }),
            'jumlah_tanggungan': forms.NumberInput(attrs={
                'class': 'form-control',
                'min'  : '1',
                'placeholder': 'Jumlah anggota keluarga yang ditanggung',
                'id'   : 'id_jumlah_tanggungan',
            }),
            'status_rumah': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_status_rumah',
            }),
            'memiliki_kip': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id'   : 'id_memiliki_kip',
                'role' : 'switch',
            }),

            # ---- Sosial ----
            'jarak_rumah': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_jarak_rumah',
            }),
        }
        labels = {
            'nilai_rata_rata'     : 'Nilai Rata-rata Rapor',
            'ranking_kelas'       : 'Ranking di Kelas',
            'persentase_hadir'    : 'Persentase Kehadiran (%)',
            'tingkat_prestasi'    : 'Tingkat Prestasi',
            'keaktifan_organisasi': 'Keaktifan Organisasi',
            'penghasilan_ortu'    : 'Penghasilan Orang Tua (Rp/bulan)',
            'jumlah_tanggungan'   : 'Jumlah Tanggungan Keluarga',
            'status_rumah'        : 'Status Kepemilikan Rumah',
            'memiliki_kip'        : 'Memiliki Kartu Indonesia Pintar (KIP)',
            'jarak_rumah'         : 'Jarak Rumah ke Sekolah',
        }

    def clean_nilai_rata_rata(self):
        """Validasi nilai rata-rata harus antara 0 dan 100."""
        nilai = self.cleaned_data.get('nilai_rata_rata')
        if nilai is not None and (nilai < 0 or nilai > 100):
            raise forms.ValidationError("Nilai rata-rata harus antara 0 dan 100.")
        return nilai

    def clean_persentase_hadir(self):
        """Validasi persentase kehadiran harus antara 0 dan 100."""
        hadir = self.cleaned_data.get('persentase_hadir')
        if hadir is not None and (hadir < 0 or hadir > 100):
            raise forms.ValidationError("Persentase kehadiran harus antara 0 dan 100.")
        return hadir

    def clean_penghasilan_ortu(self):
        """Validasi penghasilan tidak boleh negatif."""
        penghasilan = self.cleaned_data.get('penghasilan_ortu')
        if penghasilan is not None and penghasilan < 0:
            raise forms.ValidationError("Penghasilan tidak boleh bernilai negatif.")
        return penghasilan


# ============================================================
# FORM 4: DATA TRAINING
# ============================================================
class DataTrainingForm(forms.ModelForm):
    """
    Form untuk menambah/edit data training algoritma C4.5.
    """

    class Meta:
        model  = DataTraining
        fields = ['nilai', 'prestasi', 'penghasilan', 'kip', 'hasil', 'keterangan']
        widgets = {
            'nilai': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_nilai_training',
            }),
            'prestasi': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_prestasi_training',
            }),
            'penghasilan': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_penghasilan_training',
            }),
            'kip': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_kip_training',
            }),
            'hasil': forms.Select(attrs={
                'class': 'form-select',
                'id'   : 'id_hasil_training',
            }),
            'keterangan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows' : 2,
                'id'   : 'id_keterangan_training',
                'placeholder': 'Keterangan tambahan (opsional)',
            }),
        }


# ============================================================
# FORM 5: PENCARIAN SISWA
# ============================================================
class SearchForm(forms.Form):
    """Form sederhana untuk pencarian data siswa."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class'      : 'form-control',
            'placeholder': 'Cari nama atau NIS siswa...',
            'id'         : 'id_search_query',
        })
    )
