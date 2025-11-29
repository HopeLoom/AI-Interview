# Interview Simulation Framework

* This branch contains the backend code for the interview simulation. The following are the main features

1) Interview consists of multiple rounds with each round have its own set of panelists
2) Interview and panelist information is generated from job description. For now, its loaded from file. 
3) The central component that manages the whole interview process is referred to as the master agent.
4) Master Agent manages communication with the candidate/user via websocket communication while also managing the flow of information between the panelists and activity agent. It also has its own set of functionalities such as who gets to speak next, generates advice for panelists, performs rules and regulation check, ensures the interview flow is maintained, keeps track of the interview transcript.
5) Activity agent monitors the coding activity performed by the candidate during the interview. It provides analysis to the panelists.
6) Each of the panelists/agents have their own set of personalities, memories and decision making capabilites. They think, reflect and generate responses according to the interview progress and candidate responses.

* Master Agent based Two Way Asynchronous Communication 

1) Master agent acts as the mediator, facilitating all communication between itself and the other agents.
2) Agents do not communicate directly with each other but rely on the master agent to route messages.
3) Both the master agent and the other agents can send and receive messages, enabling two-way interaction.
4) Messages are sent via queues, which decouple the sending and receiving processes.
5) Agents and the master agent process messages independently, ensuring that they are not blocked while waiting for responses.
6) Agents are running within the same thread but as coroutines since none of them require CPU intensive tasks.
7) In the future, we would want to run each agent in its own thread especially if they would use tools like code editor to compile code in real time, searching domain specific knowledge online etc.

* Code Structure

1) Main.py runs the websocket service that connects with the frontend
2) Based on user login message received through the websocket, main.py creates the master agent
3) master_agent/master.py contains the code for the master agent 
4) Panelist_agent/panelist.py contains the code for the panelist agent
5) activity_agent/activity.py contains the code for activity agent
6) candidate_agent/candidate.py contains the code for the candidate side.


* Details about the Agents

Activity Agent: High Level Analysis/Code Interpretor -> Analysis with respect to Question -> Final analysis for panelist

Panelist Agent: Reason -> Domain Knowledge Access -> Respond -> Reflect -> Evaluate

Master Agent: Speaker determination -> Advice Generation -> Topic Completion -> Evaluate

* Run the application using the following

uvicorn main:app --host 0.0.0.0 --port 8000

# Hopeloom Backend Deployment Guide

This guide documents how to deploy the Hopeloom backend, which includes:
- A FastAPI WebSocket backend
- Hosted on a Google Cloud VM
- Secured using Nginx and Let's Encrypt SSL
- Accessible via `wss://api.hopeloom.com/ws`

---

## 🚀 1. VM Setup (Google Cloud)

- Create a new VM on GCP with:
  - Machine type: `e2-standard-4`
  - OS: Ubuntu 22.04 LTS
  - Disk: 10–30GB SSD
  - External IP: static or ephemeral
  - Firewall: allow HTTP (80), HTTPS (443)

- SSH into the VM:
  ```bash
  gcloud compute ssh your-vm-name --zone=your-zone

* systemd Service (Auto-start Backend)
* Create File
sudo nano /etc/systemd/system/hopeloom-backend.service
* Paste
[Unit]
Description=Hopeloom Backend WebSocket Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/hopeloom-backend
ExecStart=/home/ubuntu/anaconda3/envs/hopeloom/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

* Enable and Restart
sudo systemctl daemon-reload
sudo systemctl enable hopeloom-backend
sudo systemctl start hopeloom-backend
sudo systemctl status hopeloom-backend

sudo apt update
sudo apt install nginx -y

* Domain Setup
*Go to GoDaddy → DNS → Manage DNS for hopeloom.com
* Add A record:

## Install & Configure Nginx
* sudo apt install nginx -y
* Create Nginx site config
sudo nano /etc/nginx/sites-available/api.hopeloom.com
* paste the following contents
server {
    listen 80;
    server_name api.hopeloom.com;

    location / {
        return 301 https://$host$request_uri;
    }
}


## enable it
# Edit config
sudo nano /etc/nginx/sites-available/staging.api.hopeloom.com

# (Comment out or remove SSL server block)

# Reload nginx without SSL
sudo nginx -t
sudo systemctl reload nginx

# Issue certificate
sudo certbot --nginx -d staging.api.hopeloom.com

# nginx will be auto-updated by certbot
sudo nginx -t
sudo systemctl reload nginx

## Enable https with certbot
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.hopeloom.com


## useful commands

* Restart backend
sudo systemctl restart hopeloom-backend

* View logs
journalctl -u hopeloom-backend -f
sudo systemctl status hopeloom-backend


* Restart Nginx
sudo systemctl reload nginx


* View logs
tail -f logs/user123/latest.log
