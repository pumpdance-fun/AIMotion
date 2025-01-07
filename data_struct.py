from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class TokenImage:
    """Represents an image with its metadata"""
    # Required fields
    id: str
    file_path: str
    description: str
    
    # Optional fields with defaults
    width: int = 1920
    height: int = 1080
    format: str = "png"
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
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "created_at": self.created_at.isoformat(),
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenImage':
        """Create an Image instance from a dictionary"""
        # Handle required fields
        image_data = {
            'id': data.get('id', ''),
            'description': data.get('description', ''),
            'file_path': data.get('file_path', '')
        }
        
        # Handle optional fields
        if 'width' in data:
            image_data['width'] = data['width']
        if 'height' in data:
            image_data['height'] = data['height']
        if 'format' in data:
            image_data['format'] = data['format']
        if 'created_at' in data:
            image_data['created_at'] = datetime.fromisoformat(data['created_at'])
            
        return cls(**image_data)


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
        """Create a Dance instance from a dictionary
        
        When querying from ChromaDB, the data comes from metadata, so we need to
        reconstruct the required fields:
        - id: comes from the query results ids
        - description: comes from the documents field
        - file_path: comes from metadata
        """
        # Handle required fields
        dance_data = {
            'id': data.get('id', ''),  # ID might come from query results
            'description': data.get('description', ''),  # Description might come from documents
            'file_path': data.get('file_path', ''),
        }
        
        # Add optional fields if they exist
        optional_fields = ['style', 'dancer', 'music', 'resolution', 'duration']
        for field in optional_fields:
            if field in data:
                dance_data[field] = data[field]
                
        # Handle created_at datetime
        if 'created_at' in data:
            if isinstance(data['created_at'], str):
                dance_data['created_at'] = datetime.fromisoformat(data['created_at'])
            else:
                dance_data['created_at'] = data['created_at']
                
        return cls(**dance_data)

if __name__ == "__main__":
    dance = Dance(id="1", file_path="path/to/video.mp4", description="A girl is dancing to the song 'apt'")
    print(dance.metadata)
    print(dance.document)