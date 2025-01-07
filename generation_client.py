import redis
import json
import uuid
import time

class VideoGenerationClient:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.task_queue = "video_generation_tasks"
        self.result_queue = "video_generation_results"

    def submit_task(self, ref_image_path: str, ref_video_path: str, save_dir: str) -> str:
        """Submit a video generation task"""
        task_id = str(uuid.uuid4())
        task = {
            'task_id': task_id,
            'ref_image_path': ref_image_path,
            'ref_video_path': ref_video_path,
            'save_dir': save_dir
        }
        
        # Push task to queue
        self.redis_client.rpush(
            self.task_queue,
            json.dumps(task)
        )
        
        return task_id

    def get_result(self, task_id: str, timeout: int = 0) -> dict:
        """Get result for a specific task
        Returns None if no result is available within timeout
        """
        while timeout >= 0:
            # Check all results in queue
            for _ in range(self.redis_client.llen(self.result_queue)):
                result = self.redis_client.lindex(self.result_queue, _)
                if result:
                    result_dict = json.loads(result)
                    if result_dict['task_id'] == task_id:
                        # Remove this result from queue
                        self.redis_client.lrem(self.result_queue, 1, result)
                        return result_dict
            
            if timeout > 0:
                time.sleep(1)
                timeout -= 1
            else:
                break
                
        return None

# Example usage
if __name__ == '__main__':
    client = VideoGenerationClient()
    
    # Submit a task
    task_id = client.submit_task(
        "../dance_db/images/pepe_1.png",
        "../dance_db/videos/hiphop.mp4",
        "../dance_db/generated_videos"
    )
    print(f"Submitted task: {task_id}")
    
    # Wait for result
    result = client.get_result(task_id, timeout=300)  # 5 minute timeout
    if result:
        print(f"Task completed: {result}")
    else:
        print("Task timed out")