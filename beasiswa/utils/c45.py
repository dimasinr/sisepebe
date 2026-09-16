"""
utils/c45.py - Implementasi Algoritma C4.5 (Decision Tree) yang Bersih dan Terbaca
================================================================================
Modul ini dioptimalkan untuk keterbacaan (clean code) agar proses perhitungan 
algoritma C4.5 dapat diikuti dengan mudah, sesuai kebutuhan skripsi.
"""

import math
import json
from collections import Counter

class C45Proses:
    """
    Menangani seluruh siklus perhitungan C4.5 dalam satu alur yang jelas.
    """

    def __init__(self, training_data):
        self.dataset = training_data
        self.attributes = ['nilai', 'prestasi', 'penghasilan', 'kip']
        self.target = 'hasil'
        self.report = {
            'total_data': len(training_data),
            'distribusi': dict(Counter([d[self.target] for d in training_data])),
            'entropy_total': self._hitung_entropy([d[self.target] for d in training_data]),
            'perhitungan_atribut': {},
            'root_node': None,
            'rules': []
        }

    def _hitung_entropy(self, labels):
        """Rumus: -Σ (pi * log2(pi))"""
        if not labels: return 0.0
        counts = Counter(labels)
        total = len(labels)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return round(entropy, 6)

    def jalankan(self):
        """Menjalankan proses dari awal sampai akhir."""
        # 1. Hitung Gain untuk setiap atribut
        best_gain = -1
        
        for attr in self.attributes:
            gain, detail = self._hitung_gain_atribut(attr)
            self.report['perhitungan_atribut'][attr] = {
                'gain': gain,
                'detail': detail
            }
            if gain > best_gain:
                best_gain = gain
                self.report['root_node'] = attr

        # 2. Buat Rules berdasarkan Root Node yang terpilih
        self._generate_rules()
        
        # 3. Tambahkan key untuk kompatibilitas template lama
        self.report['atribut'] = self.report['root_node']
        self.report['cabang'] = {
            r['nilai']: {'hasil': r['hasil'], 'confidence': r['confidence']}
            for r in self.report['rules']
        }
        
        return self.report

    def _hitung_gain_atribut(self, attr_name):
        """Rumus: Gain(S,A) = Entropy(S) - Σ (|Si|/|S| * Entropy(Si))"""
        total_entropy = self.report['entropy_total']
        total_n = self.report['total_data']
        
        # Kelompokkan data berdasarkan nilai atribut
        subsets = {}
        for row in self.dataset:
            val = row[attr_name]
            if val not in subsets: subsets[val] = []
            subsets[val].append(row[self.target])
            
        detail_per_nilai = {}
        weighted_entropy_sum = 0
        
        for val, labels in subsets.items():
            n_si = len(labels)
            e_si = self._hitung_entropy(labels)
            weight = n_si / total_n
            weighted_entropy = weight * e_si
            weighted_entropy_sum += weighted_entropy
            
            detail_per_nilai[val] = {
                'jumlah': n_si,
                'distribusi': dict(Counter(labels)),
                'entropy': e_si,
                'bobot': round(weight, 4)
            }
            
        gain = round(total_entropy - weighted_entropy_sum, 6)
        return gain, detail_per_nilai

    def _generate_rules(self):
        """Menghasilkan aturan keputusan dari Root Node."""
        root = self.report['root_node']
        details = self.report['perhitungan_atribut'][root]['detail']
        
        for i, (val, info) in enumerate(details.items(), 1):
            # Ambil label mayoritas untuk rule
            hasil_dominan = max(info['distribusi'], key=info['distribusi'].get)
            confidence = (info['distribusi'][hasil_dominan] / info['jumlah']) * 100
            
            self.report['rules'].append({
                'nomor': i,
                'atribut': root,
                'nilai': val,
                'kondisi': f"IF {root.capitalize()} = {val}",
                'hasil': hasil_dominan,
                'confidence': round(confidence, 2),
                'distribusi': info['distribusi']
            })

def classify_student(student_data, c45_report):
    """
    Mengklasifikasikan siswa berdasarkan report C4.5 yang sudah dihasilkan.
    """
    root = c45_report['root_node']
    student_val = student_data.get(root)
    
    # Cari rule yang cocok
    for rule in c45_report['rules']:
        if rule['nilai'] == student_val:
            return rule['hasil']
            
    # Default ke hasil mayoritas jika tidak ada yang cocok
    return max(c45_report['distribusi'], key=c45_report['distribusi'].get)

def run_seleksi(penilaian_obj, training_queryset):
    """
    Satu fungsi utama yang merangkum seluruh proses seleksi.
    """
    # Persiapan Data Training
    dataset = list(training_queryset.values('nilai', 'prestasi', 'penghasilan', 'kip', 'hasil'))
    
    # Inisialisasi dan Jalankan C4.5
    engine = C45Proses(dataset)
    report = engine.jalankan()
    
    # Data Siswa yang akan dinilai
    siswa_data = {
        'nilai': penilaian_obj.kategori_nilai,
        'prestasi': penilaian_obj.tingkat_prestasi,
        'penghasilan': penilaian_obj.kategori_penghasilan,
        'kip': 'Ya' if penilaian_obj.memiliki_kip else 'Tidak'
    }
    
    # Klasifikasi
    status_akhir = classify_student(siswa_data, report)
    
    # Format Gain Info untuk Database (agar kompatibel dengan template lama)
    gain_info = {}
    for attr, data in report['perhitungan_atribut'].items():
        gain_info[attr] = {
            'gain': data['gain'],
            'is_root': attr == report['root_node'],
            'detail': data['detail'] # Simpan detail lebih banyak!
        }
    
    return {
        'status': status_akhir,
        'entropy_awal': report['entropy_total'],
        'root_node': report['root_node'],
        'rules_json': json.dumps(report['rules'], ensure_ascii=False),
        'gain_info_json': json.dumps(gain_info, ensure_ascii=False),
        'full_report': report
    }

# Alias untuk kebutuhan TrainingListView jika masih digunakan
def build_decision_tree(dataset):
    engine = C45Proses(dataset)
    return engine.jalankan()
