import random
import requests
import time

# URL of the robot UI server (change if not localhost)
SERVER = "http://100.73.250.34:5000" #"http://<ROBOT_UI_SERVER_IP>:5000"  # e.g., "http://192.168.1.100:5000"

def get_next_job():
    try:
        resp = requests.get(f"{SERVER}/chatbot/next", timeout=10)
        data = resp.json()
        if "job_id" in data:
            return data
    except Exception as e:
        print("Error fetching next job:", e)
    return None

def submit_result(job_id, reply, logprobs=None, expert_groups=[]):
    payload = {"job_id": job_id, "reply": reply}
    if logprobs is not None:
        payload["logprobs"] = logprobs
    if expert_groups is not None:
        payload["expert_groups"] = expert_groups
    print(f"payload: {payload}")
    try:
        resp = requests.post(f"{SERVER}/chatbot/submit", json=payload, timeout=10)
        print("Submitted result for job", job_id, ":", resp.json())
    except Exception as e:
        print("Error submitting result:", e)

def main():
    print("Model worker started. Polling for jobs...")
    fake_responses = ["Sorry I can't help you with that",
                      "That isn't something I can answer",
                      "Is there anything else that I could help you with?",
                      "That's not a question I handle, sorry"
                      ]
    while True:
        job = get_next_job()
        if job:
            print("Got job:", job)
            prompt = job["message"]
            job_id = job["job_id"]

            # --- Replace this with your model inference code ---
            # For demo, just echo the prompt and fake logprobs
            reply = random.choice(fake_responses)
            logprobs = [random.random() for _ in reply] #None  # or e.g., {"tokens": [...], "logprobs": [...]}
            expert_groups = [random.choice([0,1]) for _ in range(16)]
            # --------------------------------------------------

            submit_result(job_id, reply, logprobs, expert_groups)
        else:
            time.sleep(1)  # Wait before polling again

if __name__ == "__main__":
    main()
