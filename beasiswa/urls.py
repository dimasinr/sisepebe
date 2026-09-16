"""
urls.py - Routing URL untuk aplikasi beasiswa
"""

from django.urls import path
from . import views

app_name = 'beasiswa'

urlpatterns = [
    # ---- Auth ----
    path('login/',  views.CustomLoginView.as_view(),  name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # ---- Dashboard ----
    path('', views.DashboardView.as_view(), name='dashboard'),

    # ---- Siswa CRUD ----
    path('siswa/',views.SiswaListView.as_view(),name='siswa-list'),
    path('siswa/tambah/',views.SiswaCreateView.as_view(),name='siswa-create'),
    path('siswa/<int:pk>/edit/',views.SiswaUpdateView.as_view(),name='siswa-edit'),
    path('siswa/<int:pk>/hapus/',views.SiswaDeleteView.as_view(),name='siswa-delete'),

    # ---- Penilaian ----
    path('siswa/<int:siswa_pk>/penilaian/',views.PenilaianCreateView.as_view(), name='penilaian-create'),
    path('penilaian/<int:pk>/edit/',views.PenilaianUpdateView.as_view(), name='penilaian-edit'),

    # ---- Seleksi C4.5 ----
    path('siswa/<int:siswa_pk>/seleksi/',views.RunSeleksiView.as_view(),name='run-seleksi'),
    path('seleksi/batch/', views.RunBatchSeleksiView.as_view(), name='run-batch-seleksi'),
    path('hasil/',views.HasilSeleksiListView.as_view(),name='hasil-list'),
    path('hasil/<int:pk>/',views.HasilSeleksiDetailView.as_view(),name='hasil-detail'),

    # ---- Student Access ----
    path('login-siswa/', views.login_siswa, name='login-siswa'),
    path('pengumuman/',  views.HasilSiswaDetailView.as_view(), name='hasil-siswa'),

    # ---- Data Training ----
    path('training/',views.TrainingListView.as_view(),name='training-list'),
    path('training/tambah/',views.TrainingCreateView.as_view(),name='training-create'),
    path('training/<int:pk>/hapus/',views.TrainingDeleteView.as_view(),name='training-delete'),
    path('training/seed/',views.seed_training_data,name='training-seed'),

    # ---- Export ----
    path('export/excel/',views.export_hasil_excel,name='export-excel'),
    path('export/csv/',views.export_hasil_csv,name='export-csv'),
    path('export/print/',views.export_hasil_print,name='export-print'),
]
