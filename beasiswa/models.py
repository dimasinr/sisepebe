"""
models.py - Definisi model database untuk sistem seleksi beasiswa
Menggunakan Django ORM dengan relasi antar tabel yang sesuai ERD skripsi.
"""

from django.db import models
from django.utils import timezone


# ============================================================
# MODEL 1: DATA SISWA
# Menyimpan data pribadi siswa calon penerima beasiswa
# ============================================================
class Siswa(models.Model):
    """
    Model untuk menyimpan data siswa SMA.
    Setiap siswa memiliki data pribadi lengkap sebagai dasar seleksi.
    """

    JENIS_KELAMIN_CHOICES = [
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ]

    KELAS_CHOICES = [
        ('X', 'Kelas X'),
        ('XI', 'Kelas XI'),
        ('XII', 'Kelas XII'),
    ]

    nis        = models.CharField(max_length=20, unique=True, verbose_name="NIS")
    nama       = models.CharField(max_length=100, verbose_name="Nama Siswa")
    kelas      = models.CharField(max_length=5, choices=KELAS_CHOICES, verbose_name="Kelas")
    jenis_kelamin = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES, verbose_name="Jenis Kelamin")
    alamat     = models.TextField(verbose_name="Alamat")
    no_hp      = models.CharField(max_length=15, verbose_name="No. HP")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Dibuat")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Terakhir Diubah")

    class Meta:
        verbose_name        = "Siswa"
        verbose_name_plural = "Data Siswa"
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.nis} - {self.nama}"


# ============================================================
# MODEL 2: DATA PENILAIAN / KRITERIA BEASISWA
# Menyimpan seluruh nilai kriteria untuk setiap siswa
# Relasi: satu Siswa -> satu PenilaianBeasiswa (OneToOne)
# ============================================================
class PenilaianBeasiswa(models.Model):
    """
    Model untuk menyimpan nilai kriteria penilaian beasiswa.
    Mencakup 4 kategori: Akademik, Prestasi, Ekonomi, dan Sosial.
    """

    # ---- Pilihan untuk field kategorikal ----
    TINGKAT_NILAI_CHOICES = [
        ('Tinggi', 'Tinggi'),
        ('Sedang', 'Sedang'),
        ('Rendah', 'Rendah'),
    ]

    TINGKAT_PRESTASI_CHOICES = [
        ('Tinggi', 'Tinggi (Juara Nasional/Provinsi)'),
        ('Sedang', 'Sedang (Juara Kabupaten/Kota)'),
        ('Rendah', 'Rendah (Tidak Berprestasi)'),
    ]

    KEAKTIFAN_ORG_CHOICES = [
        ('Aktif', 'Aktif'),
        ('Cukup', 'Cukup Aktif'),
        ('Tidak', 'Tidak Aktif'),
    ]

    PENGHASILAN_CHOICES = [
        ('Rendah', 'Rendah (< Rp 2.000.000)'),
        ('Sedang', 'Sedang (Rp 2.000.000 - 4.000.000)'),
        ('Tinggi', 'Tinggi (> Rp 4.000.000)'),
    ]

    STATUS_RUMAH_CHOICES = [
        ('Milik Sendiri', 'Milik Sendiri'),
        ('Sewa', 'Sewa/Kontrak'),
        ('Menumpang', 'Menumpang'),
    ]

    JARAK_RUMAH_CHOICES = [
        ('Dekat', 'Dekat (< 5 km)'),
        ('Sedang', 'Sedang (5 - 15 km)'),
        ('Jauh', 'Jauh (> 15 km)'),
    ]

    # Relasi ke tabel Siswa (OneToOneField)
    siswa = models.OneToOneField(
        Siswa,
        on_delete=models.CASCADE,
        related_name='penilaian',
        verbose_name="Siswa"
    )

    # ---- KATEGORI AKADEMIK ----
    nilai_rata_rata  = models.FloatField(verbose_name="Nilai Rata-rata Rapor")
    ranking_kelas    = models.PositiveIntegerField(verbose_name="Ranking Kelas")
    persentase_hadir = models.FloatField(verbose_name="Persentase Kehadiran (%)")

    # Field hasil preprocessing - Kategori Akademik
    kategori_nilai   = models.CharField(
        max_length=10,
        choices=TINGKAT_NILAI_CHOICES,
        blank=True,
        verbose_name="Kategori Nilai"
    )

    # ---- KATEGORI PRESTASI ----
    tingkat_prestasi   = models.CharField(max_length=10, choices=TINGKAT_PRESTASI_CHOICES, verbose_name="Tingkat Prestasi")
    keaktifan_organisasi = models.CharField(max_length=10, choices=KEAKTIFAN_ORG_CHOICES, verbose_name="Keaktifan Organisasi")

    # ---- KATEGORI EKONOMI ----
    penghasilan_ortu   = models.BigIntegerField(verbose_name="Penghasilan Orang Tua (Rp)")
    jumlah_tanggungan  = models.PositiveIntegerField(verbose_name="Jumlah Tanggungan Keluarga")
    status_rumah       = models.CharField(max_length=20, choices=STATUS_RUMAH_CHOICES, verbose_name="Status Rumah")
    memiliki_kip       = models.BooleanField(default=False, verbose_name="Memiliki KIP")

    # Field hasil preprocessing - Kategori Ekonomi
    kategori_penghasilan = models.CharField(
        max_length=10,
        choices=PENGHASILAN_CHOICES,
        blank=True,
        verbose_name="Kategori Penghasilan"
    )

    # ---- KATEGORI SOSIAL ----
    jarak_rumah = models.CharField(max_length=10, choices=JARAK_RUMAH_CHOICES, verbose_name="Jarak Rumah ke Sekolah")

    # ---- TIMESTAMP ----
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Penilaian Beasiswa"
        verbose_name_plural = "Data Penilaian Beasiswa"
        ordering            = ['-created_at']

    def __str__(self):
        return f"Penilaian - {self.siswa.nama}"

    def save(self, *args, **kwargs):
        """
        Override save() untuk menjalankan preprocessing otomatis
        sebelum data disimpan ke database.
        """
        # Preprocessing: Klasifikasi kategori nilai
        self.kategori_nilai = self._klasifikasi_nilai(self.nilai_rata_rata)

        # Preprocessing: Klasifikasi kategori penghasilan
        self.kategori_penghasilan = self._klasifikasi_penghasilan(self.penghasilan_ortu)

        super().save(*args, **kwargs)

    @staticmethod
    def _klasifikasi_nilai(nilai):
        """
        Mengklasifikasikan nilai rata-rata ke kategori:
        - Tinggi : >= 90
        - Sedang : 80 - 89
        - Rendah : < 80
        """
        if nilai >= 90:
            return 'Tinggi'
        elif nilai >= 80:
            return 'Sedang'
        else:
            return 'Rendah'

    @staticmethod
    def _klasifikasi_penghasilan(penghasilan):
        """
        Mengklasifikasikan penghasilan orang tua ke kategori:
        - Rendah : < 2.000.000
        - Sedang : 2.000.000 - 4.000.000
        - Tinggi : > 4.000.000
        """
        if penghasilan < 2_000_000:
            return 'Rendah'
        elif penghasilan <= 4_000_000:
            return 'Sedang'
        else:
            return 'Tinggi'


# ============================================================
# MODEL 3: DATA TRAINING
# Dataset latih untuk membangun pohon keputusan C4.5
# ============================================================
class DataTraining(models.Model):
    """
    Model untuk menyimpan dataset pelatihan algoritma C4.5.
    Data ini digunakan untuk membangun pohon keputusan.
    """

    NILAI_CHOICES = [('Tinggi', 'Tinggi'), ('Sedang', 'Sedang'), ('Rendah', 'Rendah')]
    PRESTASI_CHOICES = [('Tinggi', 'Tinggi'), ('Sedang', 'Sedang'), ('Rendah', 'Rendah')]
    PENGHASILAN_CHOICES = [('Rendah', 'Rendah'), ('Sedang', 'Sedang'), ('Tinggi', 'Tinggi')]
    KIP_CHOICES = [('Ya', 'Ya'), ('Tidak', 'Tidak')]
    HASIL_CHOICES = [('Diterima', 'Diterima'), ('Ditolak', 'Ditolak')]

    nilai       = models.CharField(max_length=10, choices=NILAI_CHOICES, verbose_name="Kategori Nilai")
    prestasi    = models.CharField(max_length=10, choices=PRESTASI_CHOICES, verbose_name="Kategori Prestasi")
    penghasilan = models.CharField(max_length=10, choices=PENGHASILAN_CHOICES, verbose_name="Kategori Penghasilan")
    kip         = models.CharField(max_length=10, choices=KIP_CHOICES, verbose_name="Kepemilikan KIP")
    hasil       = models.CharField(max_length=15, choices=HASIL_CHOICES, verbose_name="Hasil Klasifikasi")
    keterangan  = models.TextField(blank=True, verbose_name="Keterangan")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Data Training"
        verbose_name_plural = "Dataset Training"
        ordering            = ['id']

    def __str__(self):
        return f"Training #{self.id} - {self.hasil}"


# ============================================================
# MODEL 4: HASIL SELEKSI
# Menyimpan hasil akhir seleksi beserta detail perhitungan C4.5
# Relasi: satu PenilaianBeasiswa -> satu HasilSeleksi (OneToOne)
# ============================================================
class HasilSeleksi(models.Model):
    """
    Model untuk menyimpan hasil akhir seleksi beasiswa.
    Menyimpan status penerimaan beserta ringkasan hasil perhitungan C4.5.
    """

    STATUS_CHOICES = [
        ('Diterima', 'Diterima'),
        ('Ditolak', 'Ditolak'),
    ]

    # Relasi ke tabel PenilaianBeasiswa
    penilaian = models.OneToOneField(
        PenilaianBeasiswa,
        on_delete=models.CASCADE,
        related_name='hasil_seleksi',
        verbose_name="Penilaian"
    )

    status_seleksi  = models.CharField(max_length=15, choices=STATUS_CHOICES, verbose_name="Status Seleksi")
    entropy_awal    = models.FloatField(verbose_name="Entropy Awal (S)")
    root_node       = models.CharField(max_length=50, verbose_name="Root Node Terpilih")
    rules_json      = models.TextField(verbose_name="Rules Keputusan (JSON)")  # Disimpan sebagai JSON string
    gain_info_json  = models.TextField(verbose_name="Gain per Atribut (JSON)")  # Ringkasan gain tiap atribut
    tanggal_seleksi = models.DateTimeField(default=timezone.now, verbose_name="Tanggal Seleksi")
    keterangan      = models.TextField(blank=True, verbose_name="Keterangan Tambahan")

    class Meta:
        verbose_name        = "Hasil Seleksi"
        verbose_name_plural = "Hasil Seleksi"
        ordering            = ['-tanggal_seleksi']

    def __str__(self):
        return f"{self.penilaian.siswa.nama} - {self.status_seleksi}"

    @property
    def rules(self):
        """Mengembalikan list rules dari JSON string."""
        try:
            import json
            return json.loads(self.rules_json)
        except:
            return []

    @property
    def gain_info(self):
        """Mengembalikan dict gain info dari JSON string."""
        try:
            import json
            return json.loads(self.gain_info_json)
        except:
            return {}
