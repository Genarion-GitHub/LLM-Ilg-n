import os
import json
from datetime import datetime

class FileManager:
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        
    def get_job_data(self, company_id: str, job_id: str, data_type: str):
        """Job verilerini okur (JobAd, Q&A, Quiz)"""
        file_path = os.path.join(self.base_dir, company_id, job_id, f"{data_type}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def get_candidate_data(self, company_id: str, job_id: str, candidate_id: str, data_type: str):
        """Aday verilerini okur"""
        file_path = os.path.join(self.base_dir, company_id, job_id, candidate_id, f"{data_type}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def save_candidate_data(self, company_id: str, job_id: str, candidate_id: str, data_type: str, data: dict):
        """Aday verilerini kaydeder"""
        candidate_folder = os.path.join(self.base_dir, company_id, job_id, candidate_id)
        os.makedirs(candidate_folder, exist_ok=True)
        
        file_path = os.path.join(candidate_folder, f"{data_type}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def create_candidate_folder(self, company_id: str, job_id: str, candidate_data: dict):
        """Yeni aday klasörü oluşturur"""
        job_folder = os.path.join(self.base_dir, company_id, job_id)
        
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