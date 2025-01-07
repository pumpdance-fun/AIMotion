import redis
import json
import uuid
import time

class VideoGenerationClient:
    def __init__(self, port: int = 6379, client_id: str = None):
        self.client_id = client_id or f"client_{port}"
        try:
            self.redis_client = redis.Redis(host='localhost', port=port, db=0)
            self.redis_client.ping()
            print(f"Client {self.client_id} connected to Redis on port {port}")
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis on port {port}. Make sure Redis server is running.")
            raise
        # These queue names should match the service
        self.task_queue = "video_generation_tasks"
        self.result_queue = "video_generation_results"

    def submit_task(self, ref_image_path: str, ref_video_path: str, save_dir: str) -> str:
        """Submit a video generation task"""
        task_id = str(uuid.uuid4())
        task = {
            'task_id': task_id,
            'ref_image_path': ref_image_path,
            'ref_video_path': ref_video_path,
            'save_dir': save_dir,
            'client_id': self.client_id,
            'submitted_at': time.time()
        }
        
        # Check if this task is already in the queue
        queue_length = self.redis_client.llen(self.task_queue)
        for i in range(queue_length):
            existing_task = self.redis_client.lindex(self.task_queue, i)
            if existing_task:
                existing_dict = json.loads(existing_task)
                if (existing_dict['ref_image_path'] == ref_image_path and 
                    existing_dict['ref_video_path'] == ref_video_path):
                    print(f"Similar task already in queue, returning existing task_id: {existing_dict['task_id']}")
                    return existing_dict['task_id']
        
        try:
            self.redis_client.rpush(
                self.task_queue,
                json.dumps(task)
            )
            print(f"Client {self.client_id} submitted task: {task_id}")
        except redis.ConnectionError as e:
            print(f"Failed to submit task: {e}")
            raise
        
        return task_id

    def get_result(self, task_id: str, timeout: int = 0) -> dict:
        """Get result for a specific task"""
        start_time = time.time()
        last_status = None
        
        while True:  # Changed from while timeout >= 0
            try:
                # Check all results in queue
                queue_length = self.redis_client.llen(self.result_queue)
                for i in range(queue_length):
                    result = self.redis_client.lindex(self.result_queue, i)
                    if result:
                        result_dict = json.loads(result)
                        if result_dict['task_id'] == task_id:
                            # Only remove and return if status is completed or failed
                            if result_dict['status'] in ['completed', 'failed']:
                                self.redis_client.lrem(self.result_queue, 1, result)
                                return result_dict
                            # Show processing status if different from last status
                            elif result_dict['status'] != last_status:
                                last_status = result_dict['status']
                                print(f"Task {task_id} status: {result_dict['status']} "
                                    f"(Service: {result_dict.get('service_id', 'unknown')})")
                
                # Check if we've exceeded the timeout
                if timeout > 0 and (time.time() - start_time) >= timeout:
                    break
                    
                time.sleep(1)
                    
            except redis.ConnectionError as e:
                print(f"Connection error while getting results: {e}")
                time.sleep(1)
                if timeout > 0 and (time.time() - start_time) >= timeout:
                    break
        
        return None

# Example usage
if __name__ == '__main__':
    # Create multiple clients with different tasks
    client_configs = [
        {
            "client": VideoGenerationClient(port=6379, client_id="client_1"),
            "ref_image": "~/Documents/AnyDesk/anydesk/assets/images/ai16z.png",
            "ref_video": "~/Documents/AnyDesk/anydesk/assets/videos/dance.mp4"
        },
        {
            "client": VideoGenerationClient(port=6380, client_id="client_2"),
            "ref_image": "~/Documents/AnyDesk/anydesk/assets/images/doge.jpeg",
            "ref_video": "~/Documents/AnyDesk/anydesk/assets/videos/apt.mp4"
        },
        # {
        #     "client": VideoGenerationClient(port=6381, client_id="client_3"),
        #     "ref_image": "~/Documents/AnyDesk/anydesk/assets/images/pepe.jpeg",
        #     "ref_video": "~/Documents/AnyDesk/anydesk/assets/videos/hiphop.mp4"
        # }
    ]
    
    tasks = []
    save_dir = "~/Documents/AnyDesk/anydesk/assets/generated_videos"
    
    # Submit different tasks from different clients
    for config in client_configs:
        task_id = config["client"].submit_task(
            ref_image_path=config["ref_image"],
            ref_video_path=config["ref_video"],
            save_dir=save_dir
        )
        tasks.append((config["client"], task_id))
    
    # Wait for all results
    for client, task_id in tasks:
        print(f"\nWaiting for result from {client.client_id}, task {task_id}")
        result = client.get_result(task_id, timeout=300)  # 5 minute timeout
        
        if result:
            print(f"Task completed for {client.client_id}: {result}")
        else:
            print(f"Task timed out for {client.client_id}")