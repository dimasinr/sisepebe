"""
views.py - Views untuk sistem seleksi beasiswa
================================================
Menggunakan Class-Based Views (CBV) Django.
Semua views dilindungi dengan LoginRequiredMixin.
"""

import json
import io
import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
)
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator

from .models import Siswa, PenilaianBeasiswa, DataTraining, HasilSeleksi
from .forms import LoginForm, SiswaForm, PenilaianForm, DataTrainingForm, SearchForm
from .utils.c45 import run_seleksi, build_decision_tree


# ============================================================
# AUTHENTICATION VIEWS
# ============================================================

class CustomLoginView(LoginView):
    """View login custom dengan form yang sudah di-style Bootstrap."""
    form_class    = LoginForm
    template_name = 'beasiswa/auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('beasiswa:dashboard')


class CustomLogoutView(LogoutView):
    """View logout - redirect ke halaman login."""
    next_page = reverse_lazy('beasiswa:login')


# ============================================================
# DASHBOARD VIEW
# ============================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard admin menampilkan statistik dan ringkasan seleksi."""
    template_name = 'beasiswa/dashboard.html'
    login_url     = reverse_lazy('beasiswa:login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        total_siswa    = Siswa.objects.count()
        total_diterima = HasilSeleksi.objects.filter(status_seleksi='Diterima').count()
        total_ditolak  = HasilSeleksi.objects.filter(status_seleksi='Ditolak').count()
        total_belum    = total_siswa - (total_diterima + total_ditolak)

        # Data chart per kelas
        per_kelas = (
            Siswa.objects.values('kelas')
            .annotate(jumlah=Count('id'))
            .order_by('kelas')
        )

        # Data chart status seleksi
        persen_diterima = (
            round((total_diterima / total_siswa) * 100, 1)
            if total_siswa > 0 else 0
        )

        # 5 seleksi terbaru
        seleksi_terbaru = (
            HasilSeleksi.objects
            .select_related('penilaian__siswa')
            .order_by('-tanggal_seleksi')[:5]
        )

        ctx.update({
            'total_siswa'    : total_siswa,
            'total_diterima' : total_diterima,
            'total_ditolak'  : total_ditolak,
            'total_belum'    : total_belum,
            'persen_diterima': persen_diterima,
            'per_kelas_json' : json.dumps(list(per_kelas)),
            'seleksi_terbaru': seleksi_terbaru,
        })
        return ctx


# ============================================================
# SISWA VIEWS (CRUD)
# ============================================================

class SiswaListView(LoginRequiredMixin, ListView):
    """Menampilkan daftar semua siswa dengan search dan pagination."""
    model               = Siswa
    template_name       = 'beasiswa/siswa/list.html'
    context_object_name = 'siswa_list'
    paginate_by         = 10
    login_url           = reverse_lazy('beasiswa:login')

    def get_queryset(self):
        qs    = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(
                Q(nama__icontains=query) | Q(nis__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_form'] = SearchForm(self.request.GET)
        ctx['query']       = self.request.GET.get('q', '')
        return ctx


class SiswaCreateView(LoginRequiredMixin, CreateView):
    """Form tambah data siswa baru."""
    model         = Siswa
    form_class    = SiswaForm
    template_name = 'beasiswa/siswa/form.html'
    success_url   = reverse_lazy('beasiswa:siswa-list')
    login_url     = reverse_lazy('beasiswa:login')

    def form_valid(self, form):
        messages.success(self.request, f'Data siswa "{form.instance.nama}" berhasil ditambahkan.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx        = super().get_context_data(**kwargs)
        ctx['judul'] = 'Tambah Data Siswa'
        ctx['aksi']  = 'Simpan'
        return ctx


class SiswaUpdateView(LoginRequiredMixin, UpdateView):
    """Form edit data siswa."""
    model         = Siswa
    form_class    = SiswaForm
    template_name = 'beasiswa/siswa/form.html'
    success_url   = reverse_lazy('beasiswa:siswa-list')
    login_url     = reverse_lazy('beasiswa:login')

    def form_valid(self, form):
        messages.success(self.request, f'Data siswa "{form.instance.nama}" berhasil diperbarui.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx        = super().get_context_data(**kwargs)
        ctx['judul'] = 'Edit Data Siswa'
        ctx['aksi']  = 'Perbarui'
        return ctx


class SiswaDeleteView(LoginRequiredMixin, DeleteView):
    """Hapus data siswa."""
    model         = Siswa
    template_name = 'beasiswa/siswa/confirm_delete.html'
    success_url   = reverse_lazy('beasiswa:siswa-list')
    login_url     = reverse_lazy('beasiswa:login')

    def form_valid(self, form):
        nama = self.object.nama
        messages.success(self.request, f'Data siswa "{nama}" berhasil dihapus.')
        return super().form_valid(form)


# ============================================================
# PENILAIAN VIEWS
# ============================================================

class PenilaianCreateView(LoginRequiredMixin, CreateView):
    """Form input data penilaian/kriteria untuk satu siswa."""
    model         = PenilaianBeasiswa
    form_class    = PenilaianForm
    template_name = 'beasiswa/penilaian/form.html'
    login_url     = reverse_lazy('beasiswa:login')

    def dispatch(self, request, *args, **kwargs):
        self.siswa = get_object_or_404(Siswa, pk=kwargs['siswa_pk'])
        # Cegah duplikasi penilaian
        if hasattr(self.siswa, 'penilaian'):
            messages.warning(request, 'Siswa ini sudah memiliki data penilaian. Gunakan menu edit.')
            return redirect('beasiswa:penilaian-edit', pk=self.siswa.penilaian.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.siswa = self.siswa
        messages.success(self.request, f'Data penilaian untuk "{self.siswa.nama}" berhasil disimpan.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('beasiswa:siswa-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['siswa'] = self.siswa
        ctx['judul'] = f'Input Penilaian - {self.siswa.nama}'
        return ctx


class PenilaianUpdateView(LoginRequiredMixin, UpdateView):
    """Form edit data penilaian."""
    model         = PenilaianBeasiswa
    form_class    = PenilaianForm
    template_name = 'beasiswa/penilaian/form.html'
    success_url   = reverse_lazy('beasiswa:siswa-list')
    login_url     = reverse_lazy('beasiswa:login')

    def form_valid(self, form):
        messages.success(self.request, 'Data penilaian berhasil diperbarui.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['siswa'] = self.object.siswa
        ctx['judul'] = f'Edit Penilaian - {self.object.siswa.nama}'
        return ctx


# ============================================================
# SELEKSI VIEWS
# ============================================================

class RunSeleksiView(LoginRequiredMixin, View):
    """Menjalankan algoritma C4.5 untuk satu siswa dan menyimpan hasilnya."""
    login_url = reverse_lazy('beasiswa:login')

    def post(self, request, siswa_pk):
        siswa = get_object_or_404(Siswa, pk=siswa_pk)

        if not hasattr(siswa, 'penilaian'):
            messages.error(request, 'Siswa belum memiliki data penilaian.')
            return redirect('beasiswa:siswa-list')

        training_data = DataTraining.objects.all()
        if training_data.count() < 2:
            messages.error(request, 'Data training minimal 2 record.')
            return redirect('beasiswa:training-list')

        # Jalankan algoritma C4.5 (One-function call)
        hasil = run_seleksi(siswa.penilaian, training_data)

        # Simpan hasil
        HasilSeleksi.objects.update_or_create(
            penilaian=siswa.penilaian,
            defaults={
                'status_seleksi' : hasil['status'],
                'entropy_awal'   : hasil['entropy_awal'],
                'root_node'      : hasil['root_node'],
                'rules_json'     : hasil['rules_json'],
                'gain_info_json' : hasil['gain_info_json'],
                'keterangan'     : f'Dihitung dengan {training_data.count()} data training.',
            }
        )

        messages.success(request, f'Seleksi selesai: {siswa.nama} dinyatakan {hasil["status"]}.')
        return redirect('beasiswa:hasil-detail', pk=siswa.penilaian.hasil_seleksi.pk)


class HasilSeleksiListView(LoginRequiredMixin, ListView):
    """Menampilkan semua hasil seleksi dengan filter dan pagination."""
    model               = HasilSeleksi
    template_name       = 'beasiswa/hasil/list.html'
    context_object_name = 'hasil_list'
    paginate_by         = 10
    login_url           = reverse_lazy('beasiswa:login')

    def get_queryset(self):
        qs     = super().get_queryset().select_related('penilaian__siswa')
        status = self.request.GET.get('status', '')
        query  = self.request.GET.get('q', '').strip()

        if status in ('Diterima', 'Ditolak'):
            qs = qs.filter(status_seleksi=status)
        if query:
            qs = qs.filter(penilaian__siswa__nama__icontains=query)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_filter'] = self.request.GET.get('status', '')
        ctx['query']         = self.request.GET.get('q', '')
        return ctx


class HasilSeleksiDetailView(LoginRequiredMixin, DetailView):
    """Menampilkan detail hasil seleksi termasuk perhitungan C4.5."""
    model               = HasilSeleksi
    template_name       = 'beasiswa/hasil/detail.html'
    context_object_name = 'hasil'
    login_url           = reverse_lazy('beasiswa:login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Data rules dan gain_info otomatis tersedia via property di model
        ctx['rules']     = self.object.rules
        ctx['gain_info'] = self.object.gain_info
        return ctx


# ============================================================
# DATA TRAINING VIEWS
# ============================================================

class TrainingListView(LoginRequiredMixin, ListView):
    """Daftar semua data training."""
    model               = DataTraining
    template_name       = 'beasiswa/training/list.html'
    context_object_name = 'training_list'
    login_url           = reverse_lazy('beasiswa:login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Tampilkan ringkasan pohon keputusan dari data training saat ini
        dataset = list(DataTraining.objects.values('nilai', 'prestasi', 'penghasilan', 'kip', 'hasil'))
        if dataset:
            ctx['tree_result'] = build_decision_tree(dataset)
        return ctx


class TrainingCreateView(LoginRequiredMixin, CreateView):
    """Tambah data training baru."""
    model         = DataTraining
    form_class    = DataTrainingForm
    template_name = 'beasiswa/training/form.html'
    success_url   = reverse_lazy('beasiswa:training-list')
    login_url     = reverse_lazy('beasiswa:login')

    def form_valid(self, form):
        messages.success(self.request, 'Data training berhasil ditambahkan.')
        return super().form_valid(form)


class TrainingDeleteView(LoginRequiredMixin, DeleteView):
    """Hapus data training."""
    model         = DataTraining
    template_name = 'beasiswa/training/confirm_delete.html'
    success_url   = reverse_lazy('beasiswa:training-list')
    login_url     = reverse_lazy('beasiswa:login')

    def form_valid(self, form):
        messages.success(self.request, 'Data training berhasil dihapus.')
        return super().form_valid(form)


# ============================================================
# EXPORT VIEWS
# ============================================================

@login_required(login_url='/login/')
def export_hasil_csv(request):
    """Export hasil seleksi ke file CSV (dapat dibuka di Excel)."""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="hasil_seleksi_beasiswa.csv"'

    writer = csv.writer(response)
    # Header kolom
    writer.writerow([
        'No', 'NIS', 'Nama Siswa', 'Kelas', 'Jenis Kelamin',
        'Nilai Rata-rata', 'Kategori Nilai', 'Tingkat Prestasi',
        'Penghasilan Ortu', 'Kategori Penghasilan', 'Memiliki KIP',
        'Root Node', 'Status Seleksi', 'Tanggal Seleksi'
    ])

    hasil_list = (
        HasilSeleksi.objects
        .select_related('penilaian__siswa')
        .order_by('-tanggal_seleksi')
    )

    for i, h in enumerate(hasil_list, start=1):
        p = h.penilaian
        s = p.siswa
        writer.writerow([
            i,
            s.nis,
            s.nama,
            s.get_kelas_display(),
            s.get_jenis_kelamin_display(),
            p.nilai_rata_rata,
            p.kategori_nilai,
            p.get_tingkat_prestasi_display(),
            f"Rp {p.penghasilan_ortu:,}",
            p.kategori_penghasilan,
            'Ya' if p.memiliki_kip else 'Tidak',
            h.root_node,
            h.status_seleksi,
            h.tanggal_seleksi.strftime('%d/%m/%Y %H:%M'),
        ])

    return response


@login_required(login_url='/login/')
def export_hasil_print(request):
    """Tampilan cetak (print) hasil seleksi."""
    hasil_list = (
        HasilSeleksi.objects
        .select_related('penilaian__siswa')
        .order_by('-tanggal_seleksi')
    )
    return render(request, 'beasiswa/hasil/print.html', {'hasil_list': hasil_list})


@login_required(login_url='/login/')
def seed_training_data(request):
    """Isi data training awal (contoh dataset dari skripsi)."""
    if request.method == 'POST':
        if DataTraining.objects.exists():
            messages.warning(request, 'Data training sudah ada. Hapus dulu jika ingin mengisi ulang.')
            return redirect('beasiswa:training-list')

        sample_data = [
            {'nilai': 'Tinggi', 'prestasi': 'Tinggi', 'penghasilan': 'Rendah', 'kip': 'Ya',    'hasil': 'Diterima', 'keterangan': 'Contoh data 1'},
            {'nilai': 'Tinggi', 'prestasi': 'Sedang', 'penghasilan': 'Rendah', 'kip': 'Ya',    'hasil': 'Diterima', 'keterangan': 'Contoh data 2'},
            {'nilai': 'Sedang', 'prestasi': 'Sedang', 'penghasilan': 'Sedang', 'kip': 'Ya',    'hasil': 'Diterima', 'keterangan': 'Contoh data 3'},
            {'nilai': 'Rendah', 'prestasi': 'Rendah', 'penghasilan': 'Tinggi', 'kip': 'Tidak', 'hasil': 'Ditolak',  'keterangan': 'Contoh data 4'},
            {'nilai': 'Sedang', 'prestasi': 'Rendah', 'penghasilan': 'Tinggi', 'kip': 'Tidak', 'hasil': 'Ditolak',  'keterangan': 'Contoh data 5'},
            {'nilai': 'Tinggi', 'prestasi': 'Sedang', 'penghasilan': 'Sedang', 'kip': 'Ya',    'hasil': 'Diterima', 'keterangan': 'Contoh data 6'},
        ]

        for item in sample_data:
            DataTraining.objects.create(**item)

        messages.success(request, f'{len(sample_data)} data training berhasil ditambahkan.')
        return redirect('beasiswa:training-list')


# ============================================================
# STUDENT VIEWS
# ============================================================

def login_siswa(request):
    """View untuk login siswa menggunakan NIS."""
    if request.method == 'POST':
        nis = request.POST.get('nis', '').strip()
        siswa = Siswa.objects.filter(nis=nis).first()
        
        if siswa:
            request.session['student_nis'] = siswa.nis
            request.session['student_id'] = siswa.id
            messages.success(request, f'Selamat datang, {siswa.nama}!')
            return redirect('beasiswa:hasil-siswa')
        else:
            messages.error(request, 'NIS tidak ditemukan. Silakan hubungi admin.')
            return redirect('beasiswa:login')
    return redirect('beasiswa:login')


class HasilSiswaDetailView(DetailView):
    """View detail hasil seleksi khusus untuk akses siswa."""
    model = HasilSeleksi
    template_name = 'beasiswa/hasil/siswa_detail.html'
    context_object_name = 'hasil'

    def get_object(self, queryset=None):
        student_id = self.request.session.get('student_id')
        if not student_id:
            return None
        return HasilSeleksi.objects.filter(penilaian__siswa_id=student_id).select_related('penilaian__siswa').first()

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('student_id'):
            messages.error(request, 'Silakan login menggunakan NIS terlebih dahulu.')
            return redirect('beasiswa:login')
        
        self.object = self.get_object()
        if not self.object:
            # Jika siswa ada tapi belum ada hasil seleksi
            siswa = Siswa.objects.get(id=request.session.get('student_id'))
            return render(request, 'beasiswa/hasil/siswa_no_result.html', {'siswa': siswa})
            
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object:
            ctx['rules'] = self.object.rules
            ctx['gain_info'] = self.object.gain_info
        return ctx
