from django.core.management.base import BaseCommand
from django.db import transaction
from beasiswa.models import Siswa, PenilaianBeasiswa, DataTraining, HasilSeleksi
from beasiswa.utils.c45 import run_seleksi


class Command(BaseCommand):
    help = "Menjalankan algoritma C4.5 untuk semua data penilaian yang belum diproses (atau seluruh data)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Proses ulang SEMUA siswa (termasuk yang sudah diproses)'
        )
        parser.add_argument(
            '--kelas',
            type=str,
            choices=['X', 'XI', 'XII'],
            help='Filter proses berdasarkan tingkat kelas (X, XI, XII)'
        )

    def handle(self, *args, **options):
        training_data = DataTraining.objects.all()
        if training_data.count() < 2:
            self.stderr.write(self.style.ERROR("Error: Data training minimal harus 2 record untuk menjalankan C4.5."))
            return

        reprocess_all = options['all']
        kelas_filter = options['kelas']

        qs = PenilaianBeasiswa.objects.select_related('siswa', 'hasil_seleksi')

        if kelas_filter:
            qs = qs.filter(siswa__kelas=kelas_filter)

        if not reprocess_all:
            qs = qs.filter(hasil_seleksi__isnull=True)

        total_target = qs.count()

        if total_target == 0:
            self.stdout.write(self.style.SUCCESS("Tidak ada data penilaian yang perlu diproses."))
            return

        self.stdout.write(self.style.NOTICE(
            f"Memulai proses C4.5 untuk {total_target} siswa "
            f"({'Semua' if reprocess_all else 'Belum Diproses'}"
            f"{f', Kelas {kelas_filter}' if kelas_filter else ''})...\n"
        ))

        processed_count = 0
        diterima_count = 0
        ditolak_count = 0

        with transaction.atomic():
            for p in qs:
                hasil = run_seleksi(p, training_data)
                
                HasilSeleksi.objects.update_or_create(
                    penilaian=p,
                    defaults={
                        'status_seleksi': hasil['status'],
                        'entropy_awal': hasil['entropy_awal'],
                        'root_node': hasil['root_node'],
                        'rules_json': hasil['rules_json'],
                        'gain_info_json': hasil['gain_info_json'],
                        'keterangan': f'Dihitung dengan {training_data.count()} data training.',
                    }
                )

                if hasil['status'] == 'Diterima':
                    diterima_count += 1
                else:
                    ditolak_count += 1

                processed_count += 1
                self.stdout.write(
                    f"[{processed_count}/{total_target}] "
                    f"NIS: {p.siswa.nis:8} | {p.siswa.nama:<30} | "
                    f"Kelas: {p.siswa.kelas:3} | Status: {hasil['status']}"
                )

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"PROSES SELEKSI SELESAI!\n"
            f"Total Diproses : {processed_count}\n"
            f"Diterima       : {diterima_count}\n"
            f"Ditolak        : {ditolak_count}\n"
            f"{'='*60}"
        ))
