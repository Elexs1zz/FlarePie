import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import zipfile

@dataclass
class SimulationConfig:
    name: str
    description: str
    created_date: str
    modified_date: str
    fuel_type: str
    chamber_pressure: float
    combustion_temp: float
    initial_altitude: float
    total_mass: float
    propellant_mass: float
    mass_flow_rate: float
    time_step: float
    reference_area: float
    tags: List[str]
    version: str = "1.0"

class ProjectManager:

    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = projects_dir
        self.current_project: Optional[str] = None
        self.projects_file = os.path.join(projects_dir, "projects.json")
        self._ensure_directory()
        self.projects = self._load_projects()
    
    def _ensure_directory(self):
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)
    
    def _load_projects(self) -> Dict[str, Any]:
        if os.path.exists(self.projects_file):
            try:
                with open(self.projects_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_projects(self):
        with open(self.projects_file, 'w') as f:
            json.dump(self.projects, f, indent=4)
    
    def create_project(self, name: str, description: str = "", tags: Optional[List[str]] = None) -> str:
        if tags is None:
            tags = []
        
        project_id = f"{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        project_dir = os.path.join(self.projects_dir, project_id)
        
        if os.path.exists(project_dir):
            raise ValueError(f"Project directory already exists: {project_id}")
        
        os.makedirs(project_dir)
        
        default_config = SimulationConfig(
            name=name,
            description=description,
            created_date=datetime.now().isoformat(),
            modified_date=datetime.now().isoformat(),
            fuel_type="RP1",
            chamber_pressure=7000000,
            combustion_temp=3500,
            initial_altitude=0,
            total_mass=10000,
            propellant_mass=8000,
            mass_flow_rate=250,
            time_step=0.1,
            reference_area=1.0,
            tags=tags
        )
        
        self.projects[project_id] = {
            "name": name,
            "description": description,
            "created_date": default_config.created_date,
            "modified_date": default_config.modified_date,
            "tags": tags,
            "simulations": [default_config.name]
        }
        
        self.save_simulation_config(project_id, default_config)
        self._save_projects()
        
        return project_id
    
    def save_simulation_config(self, project_id: str, config: SimulationConfig) -> bool:
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")
        
        project_dir = os.path.join(self.projects_dir, project_id)
        config_file = os.path.join(project_dir, f"{config.name.lower().replace(' ', '_')}.json")
        
        config.modified_date = datetime.now().isoformat()
        
        with open(config_file, 'w') as f:
            json.dump(asdict(config), f, indent=4)
        
        if config.name not in self.projects[project_id]["simulations"]:
            self.projects[project_id]["simulations"].append(config.name)
        self.projects[project_id]["modified_date"] = config.modified_date
        self._save_projects()
        
        return True
    
    def load_simulation_config(self, project_id: str, config_name: str) -> Optional[SimulationConfig]:
        if project_id not in self.projects:
            return None
        
        project_dir = os.path.join(self.projects_dir, project_id)
        config_file = os.path.join(project_dir, f"{config_name.lower().replace(' ', '_')}.json")
        
        if not os.path.exists(config_file):
            return None
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                return SimulationConfig(**data)
        except (json.JSONDecodeError, KeyError):
            return None
    
    def list_projects(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": project_id,
                "name": data["name"],
                "description": data["description"],
                "created_date": data["created_date"],
                "modified_date": data["modified_date"],
                "tags": data["tags"],
                "simulation_count": len(data["simulations"])
            }
            for project_id, data in self.projects.items()
        ]
    
    def list_simulations(self, project_id: str) -> List[str]:
        if project_id not in self.projects:
            return []
        return self.projects[project_id]["simulations"]
    
    def delete_project(self, project_id: str) -> bool:
        if project_id not in self.projects:
            return False
        
        project_dir = os.path.join(self.projects_dir, project_id)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        
        del self.projects[project_id]
        self._save_projects()
        return True
    
    def export_project(self, project_id: str, export_path: str) -> bool:
        if project_id not in self.projects:
            return False
        
        project_dir = os.path.join(self.projects_dir, project_id)
        if not os.path.exists(project_dir):
            return False
        
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_dir)
                        zipf.write(file_path, arcname)
            
            zipf.writestr("project_info.json", json.dumps(self.projects[project_id], indent=4))
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def import_project(self, import_path: str) -> Optional[str]:
        try:
            with zipfile.ZipFile(import_path, 'r') as zipf:
                project_info = json.loads(zipf.read("project_info.json"))
                
                project_id = f"{project_info['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                project_dir = os.path.join(self.projects_dir, project_id)
                
                zipf.extractall(project_dir)
                
                project_info["imported_date"] = datetime.now().isoformat()
                self.projects[project_id] = project_info
                self._save_projects()
                
                return project_id
        except Exception as e:
            print(f"Import error: {e}")
            return None
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        query = query.lower()
        results = []
        
        for project_id, data in self.projects.items():
            if (query in data["name"].lower() or 
                query in data["description"].lower() or 
                any(query in tag.lower() for tag in data["tags"])):
                results.append({
                    "id": project_id,
                    "name": data["name"],
                    "description": data["description"],
                    "created_date": data["created_date"],
                    "modified_date": data["modified_date"],
                    "tags": data["tags"],
                    "simulation_count": len(data["simulations"])
                })
        
        return results 