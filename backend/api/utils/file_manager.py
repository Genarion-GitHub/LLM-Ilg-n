import os
import json
from datetime import datetime

class FileManager:
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        self._reader = None
        self._writer = None
        self._manager = None
    
    @property
    def reader(self):
        """Sadece okuma işlemleri için interface"""
        if self._reader is None:
            self._reader = FileReader(self)
        return self._reader
    
    @property
    def writer(self):
        """Sadece yazma işlemleri için interface"""
        if self._writer is None:
            self._writer = FileWriter(self)
        return self._writer
    
    @property
    def manager(self):
        """Klasör ve liste yönetimi için interface"""
        if self._manager is None:
            self._manager = FileManagerOps(self)
        return self._manager
        
    def get_job_data(self, company_id: str, job_id: str, data_type: str):
        """Job verilerini okur (JobAd, Q&A, Quiz)"""
        file_path = os.path.join(self.base_dir, job_id, f"{data_type}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def get_cv_data(self, candidate_id: str):
        """Adayın CV verilerini okur"""
        return self.get_candidate_data(candidate_id, "cv_extraction.json")
    
    def get_qna_data(self, job_id: str):
        """İş ilanının Q&A verilerini okur"""
        file_path = os.path.join(self.base_dir, job_id, "Q&A.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def get_job_ad_data(self, job_id: str):
        """İş ilanı verilerini okur"""
        file_path = os.path.join(self.base_dir, job_id, "JobAd.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_job_data(self, company_id: str, job_id: str, data_type: str, data: dict):
        """Job verilerini kaydeder (Quiz.json gibi)"""
        job_folder = os.path.join(self.base_dir, job_id)
        os.makedirs(job_folder, exist_ok=True)
        
        file_path = os.path.join(job_folder, f"{data_type}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    

    def save_candidate_data(self, company_id: str, job_id: str, candidate_id: str, data_type: str, data: dict):
        """Aday verilerini kaydeder"""
        candidate_folder = os.path.join(self.base_dir, job_id, candidate_id)
        os.makedirs(candidate_folder, exist_ok=True)
        
        file_path = os.path.join(candidate_folder, f"{data_type}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def create_candidate_folder(self, company_id: str, job_id: str, candidate_data: dict):
        """Yeni aday klasörü oluşturur"""
        job_folder = os.path.join(self.base_dir, job_id)
        
        # Mevcut aday sayısını bul
        candidate_count = self._get_next_candidate_number(job_folder)
        candidate_id = f"{job_id}-{candidate_count:05d}"
        
        # Aday klasörü oluştur
        candidate_folder = os.path.join(job_folder, candidate_id)
        os.makedirs(candidate_folder, exist_ok=True)
        
        # CV extraction kaydet
        self.save_candidate_data(company_id, job_id, candidate_id, "cv_extraction", candidate_data)
        
        # Interview list güncelle
        self._update_interview_list(job_folder, candidate_id, candidate_data)
        
        return candidate_folder
    
    def _get_next_candidate_number(self, job_folder: str) -> int:
        """Bir sonraki aday numarasını hesaplar"""
        if not os.path.exists(job_folder):
            return 1
            
        existing_folders = [f for f in os.listdir(job_folder) 
                          if os.path.isdir(os.path.join(job_folder, f)) 
                          and f.startswith("Genar-")]
        
        return len(existing_folders) + 1
    
    def _update_interview_list(self, job_folder: str, candidate_id: str, candidate_data: dict):
        """Interview_list.json dosyasını günceller"""
        interview_list_path = os.path.join(job_folder, "Interview_list.json")
        
        # Mevcut listeyi oku
        if os.path.exists(interview_list_path):
            with open(interview_list_path, 'r', encoding='utf-8') as f:
                interview_list = json.load(f)
        else:
            interview_list = {"candidates": []}
        
        # Yeni adayı ekle
        candidate_entry = {
            "candidate_id": candidate_id,
            "name": candidate_data.get("name", "Unknown"),
            "email": candidate_data.get("personal_info", {}).get("email", ""),
            "application_date": datetime.now().isoformat(),
            "status": "applied"
        }
        
        interview_list["candidates"].append(candidate_entry)
        
        # Dosyayı kaydet
        with open(interview_list_path, 'w', encoding='utf-8') as f:
            json.dump(interview_list, f, ensure_ascii=False, indent=2)
    
    def _get_paths_from_id(self, candidate_id: str):
        """Candidate ID'den ilan ve aday klasör yollarını çıkarır"""
        # Genar-00001-00001 -> ["Genar", "00001", "00001"]
        parts = candidate_id.split("-")
        if len(parts) < 3:
            raise ValueError(f"Invalid candidate_id format: {candidate_id}")
        
        # İlan kodu: Genar-00001
        job_id = f"{parts[0]}-{parts[1]}"
        
        # Yolları oluştur
        job_folder = os.path.join(self.base_dir, job_id)
        candidate_folder = os.path.join(job_folder, candidate_id)
        
        return job_folder, candidate_folder
    
    def get_candidate_file_path(self, candidate_id: str, file_name: str):
        """Adayın belirli dosyasının tam yolunu döndürür"""
        try:
            _, candidate_folder = self._get_paths_from_id(candidate_id)
            file_path = os.path.join(candidate_folder, file_name)
            
            if os.path.exists(file_path):
                return file_path
            return None
        except Exception:
            return None
    
    def get_candidate_data(self, candidate_id: str, file_name: str):
        """Adayın JSON dosyasını okur ve dictionary döndürür"""
        file_path = self.get_candidate_file_path(candidate_id, file_name)
        
        if not file_path:
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def get_all_candidate_files(self, candidate_id: str):
        """Adayın klasöründeki tüm dosyaları listeler"""
        try:
            _, candidate_folder = self._get_paths_from_id(candidate_id)
            
            if not os.path.exists(candidate_folder):
                return []
            
            # Sadece dosyaları al, klasörleri değil
            all_items = os.listdir(candidate_folder)
            files = [item for item in all_items 
                    if os.path.isfile(os.path.join(candidate_folder, item))]
            
            return files
        except Exception:
            return []

class FileReader:
    def __init__(self, file_manager):
        self.fm = file_manager
    
    def get_job_data(self, company_id: str, job_id: str, data_type: str):
        return self.fm.get_job_data(company_id, job_id, data_type)
    
    def get_cv_data(self, candidate_id: str):
        return self.fm.get_cv_data(candidate_id)
    
    def get_qna_data(self, job_id: str):
        return self.fm.get_qna_data(job_id)
    
    def get_job_ad_data(self, job_id: str):
        return self.fm.get_job_ad_data(job_id)
    
    def get_candidate_data(self, candidate_id: str, file_name: str):
        return self.fm.get_candidate_data(candidate_id, file_name)

class FileWriter:
    def __init__(self, file_manager):
        self.fm = file_manager
    
    def save_job_data(self, company_id: str, job_id: str, data_type: str, data: dict):
        return self.fm.save_job_data(company_id, job_id, data_type, data)
    
    def save_candidate_data(self, company_id: str, job_id: str, candidate_id: str, data_type: str, data: dict):
        return self.fm.save_candidate_data(company_id, job_id, candidate_id, data_type, data)

class FileManagerOps:
    def __init__(self, file_manager):
        self.fm = file_manager
    
    def create_candidate_folder(self, company_id: str, job_id: str, candidate_data: dict):
        return self.fm.create_candidate_folder(company_id, job_id, candidate_data)
    
    def get_candidate_file_path(self, candidate_id: str, file_name: str):
        return self.fm.get_candidate_file_path(candidate_id, file_name)
    
    def get_all_candidate_files(self, candidate_id: str):
        return self.fm.get_all_candidate_files(candidate_id)