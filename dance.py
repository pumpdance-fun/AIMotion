from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Dance:
    """Represents a dance video with its metadata"""
    # Required fields
    id: str
    file_path: str
    description: str
    
    # Optional fields with defaults
    style: str = ""
    dancer: str = ""
    music: str = ""
    resolution: str = "1920x1080"
    duration: int = 0  # in seconds
    created_at: datetime = datetime.now()

    
    @property
    def document(self) -> str:
        """Returns the document text for ChromaDB embedding"""
        return self.description
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Returns the metadata dictionary for ChromaDB"""
        return {
            "file_path": str(self.file_path),
            "style": self.style,
            "dancer": self.dancer,
            "music": self.music,
            "resolution": self.resolution,
            "duration": self.duration,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dance':
        """Create a Dance instance from a dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

if __name__ == "__main__":
    dance = Dance(id="1", file_path="path/to/video.mp4", description="A girl is dancing to the song 'apt'")
    print(dance.metadata)
    print(dance.document)