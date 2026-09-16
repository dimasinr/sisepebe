# pyrefly: ignore [missing-import]
from django.contrib import admin
from .models import Siswa, PenilaianBeasiswa, DataTraining, HasilSeleksi

@admin.register(Siswa)
class SiswaAdmin(admin.ModelAdmin):
    list_display = ('nis', 'nama', 'kelas', 'jenis_kelamin', 'created_at')
    search_fields = ('nis', 'nama')
    list_filter = ('kelas', 'jenis_kelamin')

@admin.register(PenilaianBeasiswa)
class PenilaianAdmin(admin.ModelAdmin):
    list_display = ('siswa', 'nilai_rata_rata', 'kategori_nilai', 'penghasilan_ortu', 'kategori_penghasilan')
    list_filter = ('kategori_nilai', 'kategori_penghasilan')
    search_fields = ('siswa__nama', 'siswa__nis')

@admin.register(DataTraining)
class DataTrainingAdmin(admin.ModelAdmin):
    list_display = ('id', 'nilai', 'prestasi', 'penghasilan', 'kip', 'hasil')
    list_filter = ('nilai', 'prestasi', 'penghasilan', 'kip', 'hasil')

@admin.register(HasilSeleksi)
class HasilSeleksiAdmin(admin.ModelAdmin):
    list_display = ('penilaian', 'status_seleksi', 'root_node', 'tanggal_seleksi')
    list_filter = ('status_seleksi', 'root_node')
    search_fields = ('penilaian__siswa__nama',)
